from pytest import fixture, raises
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from repository.database import Base
from repository.inbox import SQLAlchemyInboxRepository
from domain.models import Inbox, Message


@fixture
def db_session():
    """Sets up an isolated, in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@fixture
def repo(db_session):
    return SQLAlchemyInboxRepository(db_session)


@fixture
def sample_inbox(owner_signature):
    return Inbox.create(
        topic="Initial Topic",
        owner_signature=owner_signature,
        expires_in_hours=24,
        requires_signature=False
    )

@fixture
def owner_signature():
    return "owner#sig"


def test_save_and_get_inbox(repo, sample_inbox, owner_signature):
    repo.save_new(sample_inbox)

    fetched = repo.get_by_id(sample_inbox.id)
    assert fetched is not None
    assert fetched.topic == "Initial Topic"
    assert fetched.owner_signature == owner_signature


def test_save_duplicate_id_raises_error(repo, sample_inbox):
    repo.save_new(sample_inbox)
    with raises(ValueError, match=f"Inbox with id {sample_inbox.id} already exists"):
        repo.save_new(sample_inbox)


def test_update_inbox_topic(repo, sample_inbox):
    repo.save_new(sample_inbox)

    # Modify domain object
    new_topic = "Updated Topic"
    sample_inbox.topic = new_topic
    repo.edit_topic(sample_inbox, new_topic)

    updated = repo.get_by_id(sample_inbox.id)
    assert updated.topic == new_topic



def test_list_by_owner(repo):
    inbox1 = Inbox.create("T1", "owner#1", 1, False)
    inbox2 = Inbox.create("T2", "owner#2", 1, False)

    repo.save_new(inbox1)
    repo.save_new(inbox2)

    results = repo.list_by_owner("owner#1")
    assert len(results) == 1
    assert results[0].id == inbox1.id


def test_get_non_existent_inbox(repo):
    assert repo.get_by_id("does-not-exist") is None
