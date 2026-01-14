import secrets

from sqlalchemy.orm import Session

from domain.models import Inbox, Message
from repository.database import InboxORM, MessageORM


class InboxRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_id(self, length: int = 10) -> str:
        while True:
            new_id = secrets.token_urlsafe(length)
            exists = self.db.query(InboxORM).filter_by(id=new_id).first()
            if not exists:
                return new_id

    def save(self, inbox: Inbox):
        inbox_orm = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if not inbox_orm:
            inbox_orm = InboxORM(id=inbox.id)
            self.db.add(inbox)

        inbox_orm.topic = inbox.topic
        inbox_orm.expires_at = inbox.expires_at
        inbox_orm.owner = inbox.owner_signature
        inbox_orm.requires_signature = inbox.requires_signature

        inbox_orm.replies = [
            MessageORM(
                body=msg.body,
                timestamp=msg.timestamp,
                signature=msg.signature
            ) for msg in inbox.replies
        ]
        self.db.commit()

    def save_new(self, inbox: Inbox):
        """Save a brand-new inbox. Fail if ID exists."""
        exists = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if exists:
            raise InboxIdCollisionError(f"Inbox with id {inbox.id} already exists")

        inbox_orm = InboxORM(
            id=inbox.id,
            topic=inbox.topic,
            owner=inbox.owner_signature,
            expires_at=inbox.expires_at,
            requires_signature=inbox.requires_signature,
            replies=[
                MessageORM(
                    body=m.body,
                    timestamp=m.timestamp,
                    signature=m.signature
                )
                for m in inbox.replies
            ]
        )
        self.db.add(inbox_orm)
        self.db.commit()

    def update(self, inbox: Inbox):
        """Update an existing inbox. Must already exist."""
        inbox_orm = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if not inbox_orm:
            raise ValueError(f"Inbox with id {inbox.id} does not exist")

        inbox_orm.topic = inbox.topic
        inbox_orm.expires_at = inbox.expires_at
        inbox_orm.requires_signature = inbox.requires_signature
        inbox_orm.replies = [
            MessageORM(
                body=m.body,
                timestamp=m.timestamp,
                signature=m.signature
            )
            for m in inbox.replies
        ]
        self.db.commit()

    def get_by_id(self, inbox_id: str) -> Inbox | None:
        inbox_orm = self.db.query(InboxORM).filter_by(id=inbox_id).first()
        if not inbox_orm:
            return None

        return Inbox(
            id=inbox_orm.id,
            topic=inbox_orm.topic,
            expires_at=inbox_orm.expires_at,
            owner_signature=inbox_orm.owner_signature,
            requires_signature=inbox_orm.requires_signature,
            replies = [Message(body=msg.body, timestamp=msg.timestamp, signature=msg.signature) for msg in inbox_orm.replies]
        )
