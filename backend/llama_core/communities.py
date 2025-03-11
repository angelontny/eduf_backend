from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from datetime import datetime

from auth0.utils import VerifyToken
from models.model import Community, CommunityMember, SharedFlashcard, Flash, Base
from pydantic import BaseModel

router = APIRouter(prefix="/api/communities", tags=["Communities"])
auth = VerifyToken()

DATABASE_URL = "sqlite:///./chats.db"

# Initialize Database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CommunityCreate(BaseModel):
    name: str
    description: str | None = None

class CommunityResponse(BaseModel):
    community_id: int
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    member_count: int

class SharedFlashcardResponse(BaseModel):
    shared_id: int
    flash_id: int
    topic_name: str
    question: str
    answer: str
    shared_by: str
    shared_at: datetime

@router.post("", response_model=CommunityResponse)
def create_community(
    community: CommunityCreate,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    new_community = Community(
        name=community.name,
        description=community.description,
        created_by=user_id
    )
    db.add(new_community)
    db.flush()
    
    # Add creator as admin member
    member = CommunityMember(
        community_id=new_community.community_id,
        user_id=user_id,
        role="admin"
    )
    db.add(member)
    db.commit()
    
    return {
        **new_community.__dict__,
        "member_count": 1
    }

@router.get("", response_model=List[CommunityResponse])
def list_communities(
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    communities = db.query(Community).all()
    return [{
        **community.__dict__,
        "member_count": len(community.members)
    } for community in communities]

@router.post("/{community_id}/join")
def join_community(
    community_id: int,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    # Check if already a member
    existing_member = db.query(CommunityMember).filter(
        CommunityMember.community_id == community_id,
        CommunityMember.user_id == user_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this community")
    
    member = CommunityMember(
        community_id=community_id,
        user_id=user_id,
        role="member"
    )
    db.add(member)
    db.commit()
    
    return {"message": "Successfully joined community"}

@router.post("/{community_id}/share/{flash_id}")
def share_flashcard(
    community_id: int,
    flash_id: int,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    # Verify membership
    member = db.query(CommunityMember).filter(
        CommunityMember.community_id == community_id,
        CommunityMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Must be a member to share flashcards")
    
    # Check if flashcard exists
    flashcard = db.query(Flash).filter(Flash.flash_id == flash_id).first()
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Share the flashcard
    shared = SharedFlashcard(
        community_id=community_id,
        flash_id=flash_id,
        shared_by=user_id
    )
    db.add(shared)
    db.commit()
    
    return {"message": "Flashcard shared successfully"}

@router.get("/{community_id}/flashcards", response_model=List[SharedFlashcardResponse])
def get_community_flashcards(
    community_id: int,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    # Verify membership
    member = db.query(CommunityMember).filter(
        CommunityMember.community_id == community_id,
        CommunityMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Must be a member to view flashcards")
    
    shared_cards = db.query(SharedFlashcard, Flash).join(
        Flash, SharedFlashcard.flash_id == Flash.flash_id
    ).filter(
        SharedFlashcard.community_id == community_id
    ).all()
    
    return [{
        "shared_id": shared.shared_id,
        "flash_id": flashcard.flash_id,
        "topic_name": flashcard.topic_name,
        "question": flashcard.question,
        "answer": flashcard.answer,
        "shared_by": shared.shared_by,
        "shared_at": shared.shared_at
    } for shared, flashcard in shared_cards]
