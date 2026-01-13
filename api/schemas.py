from pydantic import BaseModel
from datetime import datetime


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


class InboxPublicRead(BaseModel):
    id: int
    topic: str
    expires_at: datetime
    require_signature: bool

class InboxOwnerRead(BaseModel):
    id: int
    topic: str
    expires_at: datetime
    require_signature: bool
    replies: list[MessageRead]