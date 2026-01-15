from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from domain.models import Inbox, Message
from repository.database import InboxORM, MessageORM

class InboxRepository(ABC):
    @abstractmethod
    def save_new(self, inbox: Inbox) -> None:
        pass

    @abstractmethod
    def edit_topic(self, inbox: Inbox, topic: str) -> None:
        pass

    @abstractmethod
    def add_message(self, inbox: Inbox, message: Message) -> None:
        pass

    @abstractmethod
    def list_all(self) -> None:
        pass

    @abstractmethod
    def list_by_signature(self, owner_signature: str) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Inbox | None:
        pass


class SQLAlchemyInboxRepository(InboxRepository):
    def __init__(self, db: Session):
        self.db = db

    def save_new(self, inbox: Inbox):
        """Save a brand-new inbox. Fail if ID exists."""
        exists = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if exists: # todo custom exceptions
            raise ValueError(f"Inbox with id {inbox.id} already exists")

        inbox_orm = InboxORM(
            id=inbox.id,
            topic=inbox.topic,
            owner_signature=inbox.owner_signature,
            expires_at=inbox.expires_at,
            requires_signature=inbox.requires_signature,
            replies=[
                MessageORM(
                    body=m.body,
                    timestamp=m.timestamp,
                    signature=m.signature
                )
                for m in inbox.messages
            ]
        )
        self.db.add(inbox_orm)
        self.db.commit()

    def edit_topic(self, inbox: Inbox, topic: str):
        """Update an existing inbox. Must already exist."""
        inbox_orm = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if not inbox_orm:
            raise ValueError(f"Inbox with id {inbox.id} does not exist")

        inbox_orm.topic = topic
        self.db.commit()

    def add_message(self, inbox: Inbox, message: Message):
        inbox_orm = self.db.query(InboxORM).filter_by(id=inbox.id).first()
        if not inbox_orm:
            raise ValueError(f"Inbox with id {inbox.id} does not exist")
        inbox_orm.replies.append(MessageORM(
            body=message.body, timestamp=message.timestamp, signature=message.signature
        ))
        self.db.commit()

    def list_all(self) -> list[Inbox]:
        orms: list[InboxORM] = self.db.query(InboxORM).all() # todo move to select for good typehints
        return [self._inbox_to_domain(inbox_orm) for inbox_orm in orms]

    def list_by_signature(self, owner_signature: str) -> list[Inbox]:
        return [
            self._inbox_to_domain(inbox_orm)
            for inbox_orm in self.db.query(InboxORM).filter_by(owner_signature=owner_signature).all()
        ]

    def get_by_id(self, inbox_id: str) -> Inbox | None:
        inbox_orm: InboxORM | None = self.db.query(InboxORM).filter_by(id=inbox_id).first()
        if not inbox_orm:
            return None

        return self._inbox_to_domain(inbox_orm)

    def _inbox_to_domain(self, orm: InboxORM) -> Inbox:
        return Inbox(
            id=orm.id,
            topic=orm.topic,
            owner_signature=orm.owner_signature,
            expires_at=orm.expires_at,
            requires_signature=orm.requires_signature,
            messages=[self._msg_to_domain(m) for m in orm.replies],
        )

    def _msg_to_domain(self, orm_msg: MessageORM) -> Message:
        return Message(
            body=orm_msg.body,
            timestamp=orm_msg.timestamp,
            signature=orm_msg.signature,
        )