from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DATABASE_URL = "sqlite:///./feedback.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class InboxORM(Base):
    __tablename__ = "inboxes"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    owner_signature = Column(String)
    expires_at = Column(DateTime)
    requires_signature = Column(Boolean)

    replies = relationship("MessageORM", back_populates="inbox", cascade="all, delete-orphan")

class MessageORM(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inbox_id = Column(String, ForeignKey("inboxes.id"))
    body = Column(String)
    timestamp = Column(DateTime)
    signature = Column(String, nullable=True)

    inbox = relationship("InboxORM", back_populates="replies")


Base.metadata.create_all(bind=engine)
