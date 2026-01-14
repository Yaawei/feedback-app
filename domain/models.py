import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta


def generate_tripcode_signature(username: str, secret: str, separator: str = "#") -> str:
    salt = "secret_salt"
    hashed = hashlib.sha256(f"{username}{secret}{salt}".encode()).hexdigest()[:10] # 10 zeby wygodniej sie czytalo
    return f"{username}{separator}{hashed}"


@dataclass
class Message:
    body: str
    timestamp: datetime = field(default_factory=datetime.now)
    signature: str | None = None

    @classmethod
    def from_username_and_secret(cls, body: str, username: str, secret: str) -> Message:
        return cls(body=body, timestamp=datetime.now(), signature=generate_tripcode_signature(username, secret))


@dataclass
class Inbox:
    id: str
    topic: str
    owner_signature: str
    requires_signature: bool
    expires_at: datetime
    messages: list[Message] = field(default_factory=list)

    @classmethod
    def create(
            cls,
            id: str,
            topic: str,
            owner_signature: str,
            expires_in_hours: int,
            requires_signature: bool,
            now: datetime | None = None,
    ):
        now = now or datetime.now()
        expires_at = now + timedelta(hours=expires_in_hours)
        return cls(
            id=id,
            topic=topic,
            owner_signature=owner_signature,
            expires_at=expires_at,
            requires_signature=requires_signature,
        )

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def is_owner(self, provided_signature: str | None) -> bool:
        return provided_signature is not None and self.owner_signature == provided_signature

    def can_edit_topic(self, provided_signature: str | None) -> bool:
        return self.is_owner(provided_signature) and len(self.messages) == 0

    def add_message(self, message: Message) -> None:
        # todo custom domain exceptions
        if self.is_expired():
            raise ValueError("Inbox is expired")

        if self.requires_signature and not message.signature:
            raise ValueError("Anonymous reply not allowed")

        self.messages.append(message)

    def edit_topic(self, new_topic: str, provided_signature: str | None) -> None:
        if not self.can_edit_topic(provided_signature):
            raise ValueError("Inbox topic edit not allowed")

        self.topic = new_topic

    def view_for(self, provided_signature: str | None) -> InboxView:
        is_owner = self.is_owner(provided_signature)
        messages = self.messages if is_owner else None
        return InboxView(inbox=self, messages=messages)


@dataclass
class InboxView:
    inbox: Inbox
    messages: list[Message] | None
