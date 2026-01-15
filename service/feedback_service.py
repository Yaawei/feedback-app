from domain.models import User, InboxView, Inbox, Message
from repository.inbox import SQLAlchemyInboxRepository, InboxRepository


class InboxNotFoundException(Exception):
    pass


class InboxNotEditableException(Exception):
    pass


class CannotAddMessageException(Exception):
    pass



class FeedbackService:
    def __init__(self, repository: InboxRepository):
        self.repository = repository

    @staticmethod
    def get_user_from_username_and_secret(username, secret) -> User:
        return User(username, secret)

    def read_inbox(self, inbox_id: str, user: User) -> InboxView:
        inbox = self.repository.get_by_id(inbox_id)
        if not inbox:
            raise InboxNotFoundException("Inbox not found")

        return inbox.view_for(user)

    def list_inboxes(self, user: User) -> list[InboxView]:
        if user.signature is None:
            inboxes = self.repository.list_all()
        else:
            inboxes = self.repository.list_by_signature(user.signature)

        return [inbox.view_for(user) for inbox in inboxes]

    def create_inbox(self, topic: str, user: User, requires_signature: bool, expires_in_hours: int) -> InboxView:
        inbox = Inbox.create(
            topic=topic,
            owner_signature=user.signature,
            requires_signature=requires_signature,
            expires_in_hours=expires_in_hours
        )
        self.repository.save_new(inbox)
        return inbox.view_for(user)

    def update_inbox_topic(self, topic: str, user: User) -> InboxView:
        inbox = self.repository.get_by_id(topic)
        if not inbox:
            raise InboxNotFoundException("Inbox not found")
        try:
            inbox.edit_topic(topic, user)
        except ValueError as e:
            raise InboxNotEditableException(str(e))

        self.repository.edit_topic(inbox, topic)
        return inbox.view_for(user)

    def add_inbox_message(self, inbox_id: str, message: str, user: User) -> Message:
        inbox = self.repository.get_by_id(inbox_id)
        if not inbox:
            raise InboxNotFoundException("Inbox not found")

        message = Message.from_user(message, user)
        try:
            inbox.add_message(message)
        except ValueError as e:
            raise CannotAddMessageException(str(e))
        self.repository.add_message(inbox, message)
        return message
