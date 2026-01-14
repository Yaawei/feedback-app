from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from repository.database import SessionLocal
from repository.inbox import InboxRepository
from domain.models import Inbox, generate_tripcode_signature, Message
from api import schemas

router = APIRouter()

def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_inbox_repository(db: Session = Depends(get_db)) -> InboxRepository:
    return InboxRepository(db)


def get_inbox_credentials(
        x_username: str | None = Header(None),
        x_secret: str | None = Header(None)
) -> schemas.InboxAccess | None:
    if not x_username and not x_secret:
        return None
    return schemas.InboxAccess(username=x_username, secret=x_username)


@router.get("/inboxes/{inbox_id}")
def read_inbox(
        inbox_id: str,
        auth: schemas.InboxAccess | None = Depends(get_inbox_credentials), # todo check if this works
        repository: InboxRepository = Depends(get_inbox_repository)
) -> schemas.InboxOwnerRead | schemas.InboxPublicRead:
    inbox = repository.get_by_id(inbox_id)
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")

    tripcode = generate_tripcode_signature(auth.username, auth.secret) if auth else None
    view = inbox.view_for(tripcode)
    if view.messages is not None:
        return schemas.InboxOwnerRead.from_domain(view)
    return schemas.InboxPublicRead.from_domain(view)


@router.get("/inboxes")
def list_inboxes(
        auth: schemas.InboxAccess | None = Depends(get_inbox_credentials),
        repository: InboxRepository = Depends(get_inbox_repository)
) -> list[schemas.InboxOwnerRead] | list[schemas.InboxPublicRead]:
    if auth:
        owner_tripcode = generate_tripcode_signature(auth.username, auth.secret)
        inboxes = repository.list_by_owner(owner_tripcode)
        inbox_views = [inbox.view_for(owner_tripcode) for inbox in inboxes]
        return [schemas.InboxOwnerRead.from_domain(view) for view in inbox_views]
    else:
        inboxes = repository.list_all()
        inbox_views = [inbox.view_for(None) for inbox in inboxes]
        return [schemas.InboxPublicRead.from_domain(view) for view in inbox_views]


@router.post("/inboxes")
def create_inbox(
        data: schemas.InboxCreate,
        repository: InboxRepository = Depends(get_inbox_repository)
) -> schemas.InboxOwnerRead:
    owner_tripcode = generate_tripcode_signature(data.username, data.secret)
    new_inbox = Inbox.create(
        id=repository.generate_id(),
        topic=data.topic,
        owner_signature=owner_tripcode,
        requires_signature=data.requires_signature,
        expires_in_hours=data.expires_in_hours
    )
    repository.save_new(new_inbox)
    return schemas.InboxOwnerRead.from_domain(new_inbox.view_for(owner_tripcode))


@router.patch("/inboxes/{inbox_id}", response_model=schemas.InboxOwnerRead)
def update_inbox(
        inbox_id: str,
        data: schemas.InboxUpdate,
        auth: schemas.InboxAccess | None = Depends(get_inbox_credentials),
        repository: InboxRepository = Depends(get_inbox_repository)
) -> schemas.InboxOwnerRead:
    if not auth:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")
    inbox = repository.get_by_id(inbox_id)
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")

    owner_tripcode = generate_tripcode_signature(auth.username, auth.secret)
    try:
        inbox.edit_topic(data.topic, owner_tripcode)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    repository.update(inbox)
    return schemas.InboxOwnerRead.from_domain(inbox.view_for(owner_tripcode))


@router.post("/inboxes/{inbox_id}/messages", response_model=schemas.MessageRead)
def create_message(
        inbox_id: str,
        data: schemas.MessageCreate,
        repository: InboxRepository = Depends(get_inbox_repository)
) -> schemas.MessageRead:
    inbox = repository.get_by_id(inbox_id)
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")

    if data.username and data.secret:
        message = Message.from_username_and_secret(data.body, data.username, data.secret)
    else:
        message = Message(data.body)

    try:
        inbox.add_message(message)
        repository.update(inbox)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.MessageRead(
        body=message.body,
        timestamp=message.timestamp,
        signature=message.signature,
    )
