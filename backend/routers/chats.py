from fastapi import APIRouter, Security, Depends, HTTPException
from auth0.utils import VerifyToken
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime

router = APIRouter(prefix="/chats", tags=["Chats"])
auth = VerifyToken()

DATABASE_URL = "sqlite:///./chats.db"

# Initialize Database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Chat Model
class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(Integer, primary_key=True, index=True)
    chat_name = Column(String, nullable=False)
    owner_id = Column(String, index=True)  # Auth0 user ID
    created_at = Column(DateTime, default=datetime.now)

# Create Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a new chat
@router.post("/new")
def create_chat(chat_name: str, db: Session = Depends(get_db), security: dict[str, str] = Security(auth.verify)):
    chat = Chat(chat_name=chat_name, owner_id=security["sub"].split("@")[0])
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"chat_id": chat.chat_id, "chat_name": chat.chat_name, "created_at": chat.created_at}

# Get all chats for the logged-in user
@router.get("")
def get_chats(db: Session = Depends(get_db), security: dict[str, str] = Security(auth.verify)):
    chats = db.query(Chat).filter(Chat.owner_id == security["sub"].split("@")[0]).all()
    return chats
