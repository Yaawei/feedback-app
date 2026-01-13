from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import MessageRead
from repository.database import SessionLocal
from repository.inbox import InboxRepository
from domain.models import Inbox, generate_tripcode, Message
from api import schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/inboxes", response_model=schemas.InboxRead)
def create_inbox(data: schemas.InboxCreate, db: Session = Depends(get_db)) -> Inbox:
    repository = InboxRepository(db)
    owner_tripcode = generate_tripcode(data.username, data.secret)
    expiry = datetime.now() + timedelta(hours=data.expires_in_hours)
    new_inbox = Inbox(
        id=repository.generate_id(),
        topic=data.topic,
        owner_signature=owner_tripcode,
        expires_at=expiry,
        requires_signature=data.requires_signature
    )
    repository.save(new_inbox)
    return new_inbox


@router.post("/inboxes/{inbox_id}/messages", response_model=schemas.MessageRead)
def create_message(inbox_id: str, data: schemas.MessageCreate, db: Session = Depends(get_db)) -> Message:
    repository = InboxRepository(db)
    inbox = repository.get_by_id(inbox_id)
    if not inbox or inbox.is_expired():
        raise HTTPException(status_code=404, detail="Inbox not found")

    if inbox.requires_signature and not (data.username and data.secret):
        raise HTTPException(status_code=403, detail="Anonymous messages not allowed")

    signature = generate_tripcode(data.username, data.secret)
    new_message = Message(body=data.body, signature=signature)
    inbox.replies.append(new_message)
    repository.save(inbox)
    return new_message
