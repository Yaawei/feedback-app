from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from repository.database import SessionLocal
from repository.inbox import SQLAlchemyInboxRepository
from api import schemas
from service.feedback_service import FeedbackService, InboxNotFoundException, InboxNotEditableException, \
    CannotAddMessageException

router = APIRouter()

def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_inbox_repository(db: Session = Depends(get_db)) -> SQLAlchemyInboxRepository:
    return SQLAlchemyInboxRepository(db)


def get_inbox_credentials(
        x_username: str | None = Header(None),
        x_secret: str | None = Header(None)
) -> schemas.InboxAccess | None:
    return schemas.InboxAccess(username=x_username, secret=x_secret)


def get_feedback_service(repository: SQLAlchemyInboxRepository = Depends(get_inbox_repository)) -> FeedbackService:
    return FeedbackService(repository)


@router.get("/inboxes/{inbox_id}")
def read_inbox(
        inbox_id: str,
        auth: schemas.InboxAccess | None = Depends(get_inbox_credentials), # todo check if this works
        feedback_service: FeedbackService = Depends(get_feedback_service)
) -> schemas.InboxOwnerRead | schemas.InboxPublicRead:
    user = feedback_service.get_user_from_username_and_secret(auth.username, auth.secret)
    try:
        view = feedback_service.read_inbox(inbox_id, user)
    except InboxNotFoundException:
        raise HTTPException(status_code=404, detail="Inbox not found")

    if view.messages is not None:
        return schemas.InboxOwnerRead.from_domain(view)
    return schemas.InboxPublicRead.from_domain(view)


@router.get("/inboxes")
def list_inboxes(
        auth: schemas.InboxAccess | None = Depends(get_inbox_credentials),
        feedback_service: FeedbackService = Depends(get_feedback_service)
) -> list[schemas.InboxOwnerRead] | list[schemas.InboxPublicRead]:
    user = feedback_service.get_user_from_username_and_secret(auth.username, auth.secret)
    views = feedback_service.list_inboxes(user)
    if user.is_anonymous():
        schema = schemas.InboxPublicRead
    else:
        schema = schemas.InboxOwnerRead
    return [schema.from_domain(view) for view in views]


@router.post("/inboxes")
def create_inbox(
        data: schemas.InboxCreate,
        feedback_service: FeedbackService = Depends(get_feedback_service)
) -> schemas.InboxOwnerRead:
    user = feedback_service.get_user_from_username_and_secret(data.username, data.secret)
    new_inbox = feedback_service.create_inbox(
        topic=data.topic,
        user=user,
        requires_signature=data.requires_signature,
        expires_in_hours=data.expires_in_hours
    )
    return schemas.InboxOwnerRead.from_domain(new_inbox)


@router.patch("/inboxes/{inbox_id}", response_model=schemas.InboxOwnerRead)
def update_inbox(
        inbox_id: str,
        data: schemas.InboxUpdate,
        feedback_service: FeedbackService = Depends(get_feedback_service)
) -> schemas.InboxOwnerRead:
    user = feedback_service.get_user_from_username_and_secret(data.username, data.secret)
    try:
        view = feedback_service.update_inbox_topic(inbox_id, user)
    except InboxNotFoundException:
        raise HTTPException(status_code=404, detail="Inbox not found")
    except InboxNotEditableException:
        raise HTTPException(status_code=400, detail="Inbox not editable")

    return schemas.InboxOwnerRead.from_domain(view)


@router.post("/inboxes/{inbox_id}/messages", response_model=schemas.MessageRead)
def create_message(
        inbox_id: str,
        data: schemas.MessageCreate,
        feedback_service: FeedbackService = Depends(get_feedback_service)
) -> schemas.MessageRead:
    user = feedback_service.get_user_from_username_and_secret(data.username, data.secret)
    try:
        msg = feedback_service.add_inbox_message(inbox_id, data.body, user)
    except InboxNotFoundException:
        raise HTTPException(status_code=404, detail="Inbox not found")
    except CannotAddMessageException:
        raise HTTPException(status_code=400, detail="Couldn't add message")

    return schemas.MessageRead(
        body=msg.body,
        timestamp=msg.timestamp,
        signature=msg.signature,
    )
