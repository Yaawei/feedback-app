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
    require_signature: bool = True


class InboxAccess(BaseModel):
    username: str
    secret: str


class InboxPublicRead(BaseModel):
    id: str
    topic: str
    expires_at: datetime
    require_signature: bool

    @classmethod
    def from_domain(cls, inbox_view: InboxView) -> InboxPublicRead:
        return cls(
            id=inbox_view.inbox.id,
            topic=inbox_view.inbox.topic,
            expires_at=inbox_view.inbox.expires_at,
            require_signature=inbox_view.inbox.requires_signature
        )


class InboxOwnerRead(InboxPublicRead):
    replies: list[MessageRead]

    @classmethod
    def from_domain(cls, inbox_view: InboxView) -> InboxOwnerRead:
        base = super().from_domain(inbox_view)
        return cls(
            **base.model_dump(),
            replies=[
                MessageRead(
                    body=message.body, timestamp=message.timestamp, signature=message.signature
                ) for message in inbox_view.messages
            ]
        )