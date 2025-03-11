from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from sqlalchemy import func

from auth0.utils import VerifyToken
from models.model import Quiz, QuizResult, UserAnalytics, Flash
from database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["Analytics"])
auth = VerifyToken()

class QuizSubmission(BaseModel):
    quiz_id: int
    selected_answer: str

class QuizResultResponse(BaseModel):
    result_id: int
    quiz_id: int
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    ai_insight: str | None
    timestamp: datetime

class UserAnalyticsResponse(BaseModel):
    total_flashcards_studied: int
    total_quizzes_taken: int
    correct_answers: int
    accuracy_percentage: float
    last_study_date: datetime | None

@router.post("/quiz/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    # Get quiz
    quiz = db.query(Quiz).filter(Quiz.question_id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check answer
    is_correct = submission.selected_answer == quiz.correct_answer
    
    # Generate AI insight
    ai_insight = None
    if not is_correct:
        ai_insight = f"The correct answer was {quiz.correct_answer}. Here's why: [AI explanation would go here]"
    
    # Record result
    result = QuizResult(
        user_id=user_id,
        quiz_id=quiz_id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct,
        ai_insight=ai_insight
    )
    db.add(result)
    
    # Update analytics
    analytics = db.query(UserAnalytics).filter(UserAnalytics.user_id == user_id).first()
    if not analytics:
        analytics = UserAnalytics(user_id=user_id)
        db.add(analytics)
    
    analytics.total_quizzes_taken += 1
    if is_correct:
        analytics.correct_answers += 1
    analytics.last_study_date = datetime.now()
    
    db.commit()
    
    return {
        "result_id": result.result_id,
        "quiz_id": quiz.question_id,
        "question": quiz.question,
        "selected_answer": submission.selected_answer,
        "correct_answer": quiz.correct_answer,
        "is_correct": is_correct,
        "ai_insight": ai_insight,
        "timestamp": result.timestamp
    }

@router.get("/quiz/{quiz_id}/results", response_model=List[QuizResultResponse])
async def get_quiz_results(
    quiz_id: int,
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    results = db.query(QuizResult, Quiz).join(
        Quiz, QuizResult.quiz_id == Quiz.question_id
    ).filter(
        QuizResult.quiz_id == quiz_id,
        QuizResult.user_id == user_id
    ).all()
    
    return [{
        "result_id": result.result_id,
        "quiz_id": quiz.question_id,
        "question": quiz.question,
        "selected_answer": result.selected_answer,
        "correct_answer": quiz.correct_answer,
        "is_correct": result.is_correct,
        "ai_insight": result.ai_insight,
        "timestamp": result.timestamp
    } for result, quiz in results]

@router.get("/analytics", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    db: Session = Depends(get_db),
    security: dict[str, str] = Security(auth.verify)
):
    user_id = security["sub"].split("@")[0]
    
    # Get or create analytics
    analytics = db.query(UserAnalytics).filter(UserAnalytics.user_id == user_id).first()
    if not analytics:
        analytics = UserAnalytics(user_id=user_id)
        db.add(analytics)
        db.commit()
    
    # Calculate accuracy percentage
    accuracy = 0.0
    if analytics.total_quizzes_taken > 0:
        accuracy = (analytics.correct_answers / analytics.total_quizzes_taken) * 100
    
    # Count studied flashcards
    flashcards_studied = db.query(func.count(Flash.flash_id)).filter(
        Flash.user_id == user_id
    ).scalar()
    
    return {
        "total_flashcards_studied": flashcards_studied,
        "total_quizzes_taken": analytics.total_quizzes_taken,
        "correct_answers": analytics.correct_answers,
        "accuracy_percentage": accuracy,
        "last_study_date": analytics.last_study_date
    }