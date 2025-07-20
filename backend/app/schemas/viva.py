from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.viva_session import VivaSessionType, VivaSessionStatus


class VivaResponseCreate(BaseModel):
    question_text: str
    response_text: Optional[str] = None
    response_audio_path: Optional[str] = None
    question_timestamp: Optional[float] = None
    response_timestamp: Optional[float] = None
    response_duration: Optional[float] = None


class VivaResponseResponse(BaseModel):
    id: int
    question_text: str
    response_text: Optional[str] = None
    response_audio_path: Optional[str] = None
    question_timestamp: Optional[float] = None
    response_timestamp: Optional[float] = None
    response_duration: Optional[float] = None
    confidence_score: Optional[float] = None
    accuracy_score: Optional[float] = None
    completeness_score: Optional[float] = None
    keywords_matched: Optional[str] = None
    ai_feedback: Optional[str] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    is_follow_up: bool = False
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True


class VivaSessionCreate(BaseModel):
    submission_id: int
    session_type: VivaSessionType


class VivaSessionUpdate(BaseModel):
    status: Optional[VivaSessionStatus] = None
    video_file_path: Optional[str] = None
    audio_file_path: Optional[str] = None
    transcript_file_path: Optional[str] = None
    duration_seconds: Optional[int] = None


class VivaSessionResponse(BaseModel):
    id: int
    submission_id: int
    student_id: int
    session_type: VivaSessionType
    status: VivaSessionStatus
    video_file_path: Optional[str] = None
    audio_file_path: Optional[str] = None
    transcript_file_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    questions_asked: int = 0
    questions_answered: int = 0
    overall_confidence_score: Optional[float] = None
    communication_score: Optional[float] = None
    technical_accuracy_score: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[str] = None
    total_score: Optional[float] = None
    max_possible_score: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    responses: List[VivaResponseResponse] = []

    class Config:
        from_attributes = True


class MockVivaRequest(BaseModel):
    assignment_id: int
    difficulty_preference: Optional[str] = "similar"  # "easier", "similar", "harder"
    question_count: Optional[int] = 5


class AIQuestionRequest(BaseModel):
    assignment_context: str
    student_answers: str
    previous_responses: Optional[List[str]] = []
    difficulty_level: str = "intermediate"
    question_type: str = "conceptual"  # "conceptual", "application", "analysis"


class AIQuestionResponse(BaseModel):
    question: str
    expected_keywords: List[str]
    follow_up_questions: List[str]
    scoring_criteria: dict
