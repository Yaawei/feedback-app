from pydantic import BaseModel
from datetime import datetime

from domain.models import InboxView


class MessageCreate(BaseModel):
    body: str
    username: str | None = None
    secret: str | None = None


class MessageRead(BaseModel):
    body: str
    timestamp: datetime
    signature: str | None


class InboxCreate(BaseModel):
    topic: str
    username: str
    secret: str
    expires_in_hours: int = 24
    requires_signature: bool = True


class InboxUpdate(BaseModel):
    topic: str


class InboxAccess(BaseModel):
    username: str
    secret: str


class InboxPublicRead(BaseModel):
    id: str
    topic: str
    expires_at: datetime
    requires_signature: bool
    owner_signature: str

    @classmethod
    def from_domain(cls, inbox_view: InboxView) -> InboxPublicRead:
        return cls(
            id=inbox_view.inbox.id,
            topic=inbox_view.inbox.topic,
            expires_at=inbox_view.inbox.expires_at,
            requires_signature=inbox_view.inbox.requires_signature,
            owner_signature=inbox_view.inbox.owner_signature
        )


class InboxOwnerRead(InboxPublicRead):
    """Extends InboxPublicRead with replies to inbox."""
    messages: list[MessageRead] | list[None]

    @classmethod
    def from_domain(cls, inbox_view: InboxView) -> InboxOwnerRead:
        return cls(
            id=inbox_view.inbox.id,
            topic=inbox_view.inbox.topic,
            expires_at=inbox_view.inbox.expires_at,
            requires_signature=inbox_view.inbox.requires_signature,
            owner_signature=inbox_view.inbox.owner_signature,
            messages=[
                MessageRead(
                    body=message.body, timestamp=message.timestamp, signature=message.signature
                ) for message in inbox_view.messages
            ] if inbox_view.messages is not None else [None]
        )