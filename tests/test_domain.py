from pytest import fixture, raises
from datetime import datetime, timedelta
from domain.models import Inbox, Message, generate_tripcode_signature, User


@fixture
def now() -> datetime:
    return datetime.now()


@fixture
def owner_signature() -> str:
    return generate_tripcode_signature("u", "s")


@fixture
def stranger_signature() -> str:
    return generate_tripcode_signature("u", "z")


@fixture
def message(now: datetime, stranger_signature: str) -> Message:
    return Message(
        body="test message",
        timestamp=now,
        signature=stranger_signature
    )


@fixture
def active_inbox_anonymous(owner_signature: str, now: datetime) -> Inbox:
    return Inbox.create(
        topic="Test topic",
        owner_signature=owner_signature,
        expires_in_hours=2,
        requires_signature=False,
        now=now
    )


@fixture
def active_inbox_signed(owner_signature: str, now: datetime) -> Inbox:
    return Inbox.create(
        topic="Test topic",
        owner_signature=owner_signature,
        expires_in_hours=2,
        requires_signature=True,
        now=now
    )


"""Tripcode tests"""
def test_tripcode_deterministic():
    a = generate_tripcode_signature("u", "s")
    b = generate_tripcode_signature("u", "s")
    assert a == b


def test_tripcode_failure():
    a = generate_tripcode_signature("u", "s")
    b = generate_tripcode_signature("u", "z")
    assert a != b


def test_tripcode_separator():
    a = generate_tripcode_signature("u", "s")
    b = a.split("#", 2)
    assert len(b) == 2


"""Message tests"""
def test_message_create_signature_from_user():
    user = User("u", "s")
    message = Message.from_user("test message", user)
    tripcode = generate_tripcode_signature("u", "s")
    assert message.signature == tripcode


"""Inbox tests"""
def test_inbox_create_sets_expiry_correctly(owner_signature: str):
    now = datetime(2025, 1, 1, 12, 0)
    inbox = Inbox.create(
        topic="t",
        owner_signature=owner_signature,
        expires_in_hours=2,
        requires_signature=True,
        now=now,
    )
    assert inbox.expires_at == now + timedelta(hours=2)


def test_inbox_is_owner(active_inbox_anonymous: Inbox, owner_signature: str, stranger_signature: str):
    assert active_inbox_anonymous.is_owner(owner_signature) is True
    assert active_inbox_anonymous.is_owner(stranger_signature) is False
    assert active_inbox_anonymous.is_owner(None) is False


def test_inbox_is_expired(active_inbox_anonymous: Inbox, now: datetime):
    assert active_inbox_anonymous.is_expired() is False

    active_inbox_anonymous.expires_at = now - timedelta(hours=2)
    assert active_inbox_anonymous.is_expired() is True


def test_inbox_add_message_success(active_inbox_anonymous: Inbox, message: Message):
    active_inbox_anonymous.add_message(message)
    assert len(active_inbox_anonymous.messages) == 1
    assert active_inbox_anonymous.messages[0].body == message.body


def test_inbox_add_message_fails_when_expired(active_inbox_anonymous: Inbox, now: datetime, message: Message):
    active_inbox_anonymous.expires_at = now - timedelta(hours=1)

    with raises(ValueError, match="Inbox is expired"):
        active_inbox_anonymous.add_message(message)


def test_inbox_signed_rejects_without_signature(active_inbox_signed: Inbox, now: datetime, message: Message):
    message.signature = None
    with raises(ValueError, match="Anonymous reply not allowed"):
        active_inbox_signed.add_message(message)


def test_inbox_edit_topic_success(active_inbox_anonymous: Inbox, owner_signature: str):
    new_topic = "New Test Topic"
    active_inbox_anonymous.edit_topic(new_topic, owner_signature)
    assert active_inbox_anonymous.topic == new_topic


def test_inbox_edit_topic_failure_wrong_signature(active_inbox_anonymous: Inbox, stranger_signature: str):
    with raises(ValueError, match="Inbox topic edit not allowed"):
        active_inbox_anonymous.edit_topic("New Topic", stranger_signature)


def test_inbox_edit_topic_failure_if_messages_inside(
        active_inbox_anonymous: Inbox,
        owner_signature: str,
        message: Message
):
    active_inbox_anonymous.add_message(message)
    with raises(ValueError, match="Inbox topic edit not allowed"):
        active_inbox_anonymous.edit_topic("New Topic", owner_signature)


def test_inbox_view_for_privacy_logic(
        active_inbox_anonymous: Inbox,
        owner_signature: str,
        stranger_signature: str,
        message: Message
):
    active_inbox_anonymous.add_message(message)
    owner_view = active_inbox_anonymous.view_for(owner_signature)
    assert owner_view.messages is not None
    assert len(owner_view.messages) == 1

    public_view = active_inbox_anonymous.view_for(stranger_signature)
    assert public_view.messages is None