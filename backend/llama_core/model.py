from sqlalchemy import ForeignKey, Float, JSON, Table, Column, String, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import enum
import secrets

class Base(DeclarativeBase):
    pass

# Association table for community members
community_members = Table(
    'community_members',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.user_id')),
    Column('community_id', ForeignKey('communities.community_id')),
)

# Association table for shared flashcards in communities
community_flashcards = Table(
    'community_flashcards',
    Base.metadata,
    Column('flash_id', ForeignKey('cards.flash_id')),
    Column('community_id', ForeignKey('communities.community_id')),
)

class CommunityRole(enum.Enum):
    OWNER = "owner"
    MODERATOR = "moderator"
    MEMBER = "member"

class CommunityVisibility(enum.Enum):
    PUBLIC = "public"  # Anyone can find and join
    PRIVATE = "private"  # Invitation only
    UNLISTED = "unlisted"  # Can join with code but won't show in search

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[str] = mapped_column(primary_key=True)  # Auth0 user ID
    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    communities: Mapped[list["Community"]] = relationship(secondary=community_members, back_populates="members")
    owned_communities: Mapped[list["Community"]] = relationship(back_populates="owner")
    community_roles: Mapped[list["CommunityMemberRole"]] = relationship(back_populates="user")
    posts: Mapped[list["CommunityPost"]] = relationship(back_populates="author")
    comments: Mapped[list["CommunityComment"]] = relationship(back_populates="author")

# Chat Model
class Chat(Base):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(primary_key=True)
    chat_name: Mapped[str] = mapped_column(nullable=False)
    owner_id: Mapped[str] = mapped_column(index=True)  # Auth0 user ID
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    flash: Mapped[list["Flash"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    ques: Mapped[list["Questions"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    quiz: Mapped[list["Quiz"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    
# Flash Cards
class Flash(Base):
    __tablename__ = "cards"

    flash_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    topic_name: Mapped[str] = mapped_column(nullable=False)
    question: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    chat: Mapped["Chat"] = relationship(back_populates="flash")

# Questions
class Questions(Base):
    __tablename__ = "questions"

    question_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    question_content: Mapped[str] = mapped_column(nullable=False)
    response: Mapped[str] = mapped_column(nullable=False)
    chat: Mapped["Chat"] = relationship(back_populates="ques")

# Quiz
class Quiz(Base):
    __tablename__ = "quiz"

    question_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.chat_id"))
    question: Mapped[str] = mapped_column(nullable=False)
    option_a: Mapped[str] = mapped_column(nullable=False)
    option_b: Mapped[str] = mapped_column(nullable=False)
    option_c: Mapped[str] = mapped_column(nullable=False)
    option_d: Mapped[str] = mapped_column(nullable=False)
    correct_answer: Mapped[str] = mapped_column(nullable=False)
    chat: Mapped["Chat"] = relationship(back_populates="quiz")
    submissions: Mapped[list["QuizSubmission"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")

# Quiz Submissions
class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    submission_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quiz.question_id"))
    user_id: Mapped[str] = mapped_column(nullable=False)
    selected_answer: Mapped[str] = mapped_column(nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    submission_time: Mapped[datetime] = mapped_column(default=datetime.now)
    time_taken: Mapped[float] = mapped_column(Float, nullable=True)  # Time taken in seconds
    quiz: Mapped["Quiz"] = relationship(back_populates="submissions")
    ai_insight: Mapped[Optional["AIInsight"]] = relationship(back_populates="quiz_submission", uselist=False)

# User Analytics
class UserAnalytics(Base):
    __tablename__ = "user_analytics"

    analytics_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(nullable=False, index=True)
    total_study_time: Mapped[float] = mapped_column(Float, default=0.0)  # In minutes
    flashcards_studied: Mapped[int] = mapped_column(default=0)
    quizzes_taken: Mapped[int] = mapped_column(default=0)
    total_correct_answers: Mapped[int] = mapped_column(default=0)
    average_quiz_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_activity: Mapped[datetime] = mapped_column(default=datetime.now)
    study_streaks: Mapped[int] = mapped_column(default=0)  # Consecutive days of activity
    favorite_topics: Mapped[List[str]] = mapped_column(JSON, default=list)
    performance_by_topic: Mapped[dict] = mapped_column(JSON, default=dict)  # Topic-wise performance

# AI Insights
class Community(Base):
    __tablename__ = "communities"
    
    community_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    topic: Mapped[str] = mapped_column(nullable=False)
    visibility: Mapped[CommunityVisibility] = mapped_column(Enum(CommunityVisibility), nullable=False)
    join_code: Mapped[str] = mapped_column(default=lambda: secrets.token_urlsafe(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    
    owner: Mapped["User"] = relationship(back_populates="owned_communities")
    members: Mapped[list["User"]] = relationship(secondary=community_members, back_populates="communities")
    member_roles: Mapped[list["CommunityMemberRole"]] = relationship(back_populates="community")
    posts: Mapped[list["CommunityPost"]] = relationship(back_populates="community")
    shared_flashcards: Mapped[list["Flash"]] = relationship(secondary=community_flashcards)

class CommunityMemberRole(Base):
    __tablename__ = "community_member_roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.community_id"))
    role: Mapped[CommunityRole] = mapped_column(Enum(CommunityRole), nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="community_roles")
    community: Mapped["Community"] = relationship(back_populates="member_roles")

class CommunityPost(Base):
    __tablename__ = "community_posts"
    
    post_id: Mapped[int] = mapped_column(primary_key=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.community_id"))
    author_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    community: Mapped["Community"] = relationship(back_populates="posts")
    author: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["CommunityComment"]] = relationship(back_populates="post", cascade="all, delete-orphan")

class CommunityComment(Base):
    __tablename__ = "community_comments"
    
    comment_id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.post_id"))
    author_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    content: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    post: Mapped["CommunityPost"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")

class AIInsight(Base):
    __tablename__ = "ai_insights"

    insight_id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("quiz_submissions.submission_id"), unique=True)
    user_id: Mapped[str] = mapped_column(nullable=False)
    quiz_submission: Mapped["QuizSubmission"] = relationship(back_populates="ai_insight")
    strength_areas: Mapped[List[str]] = mapped_column(JSON, default=list)
    improvement_areas: Mapped[List[str]] = mapped_column(JSON, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list)
    performance_trend: Mapped[str] = mapped_column(nullable=True)  # Improving, Steady, Needs Focus
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)  # AI's confidence in user's understanding
    generated_at: Mapped[datetime] = mapped_column(default=datetime.now)
