import hashlib
from datetime import datetime
from pydantic import BaseModel, Field

def generate_tripcode(username: str, secret: str, separator: str = "#") -> str:
    salt = "secret_salt"
    hashed = hashlib.sha256(f"{username}{secret}{salt}".encode()).hexdigest()[:10] # 10 zeby wygodniej sie czytalo
    return f"{username}{separator}{hashed}"


class Message(BaseModel):
    body: str
    timestamp: datetime = Field(default_factory=datetime.now)
    signature: str | None = None


class Inbox(BaseModel):
    id: str
    topic: str
    owner_signature: str
    requires_signature: bool
    expires_at: datetime
    replies: list[Message] = []

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def can_edit_topic(self) -> bool:
        return len(self.replies) == 0

    def add_reply(self, message: Message) -> None:
        if self.is_expired():
            raise ValueError("Inbox is expired")

        if self.requires_signature and not message.signature:
            raise ValueError("Signature is required")

        self.replies.append(message)

