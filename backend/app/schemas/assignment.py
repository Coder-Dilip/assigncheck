from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.assignment import DifficultyLevel, QuestionType


class AssignmentQuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.TEXT
    order_index: int
    points: int = 10
    is_required: bool = True
    options: Optional[str] = None  # JSON string for multiple choice
    correct_answer: Optional[str] = None
    hints: Optional[str] = None
    explanation: Optional[str] = None


class AssignmentQuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: QuestionType
    order_index: int
    points: int
    is_required: bool
    options: Optional[str] = None
    hints: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VivaQuestionCreate(BaseModel):
    question_text: str
    category: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    expected_keywords: Optional[str] = None  # JSON string
    follow_up_questions: Optional[str] = None  # JSON string
    scoring_rubric: Optional[str] = None  # JSON string
    is_adaptive: bool = True
    priority: int = 1


class VivaQuestionResponse(BaseModel):
    id: int
    question_text: str
    category: Optional[str] = None
    difficulty: DifficultyLevel
    expected_keywords: Optional[str] = None
    follow_up_questions: Optional[str] = None
    scoring_rubric: Optional[str] = None
    is_adaptive: bool
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    title: str
    description: str
    instructions: Optional[str] = None
    topic: Optional[str] = None
    concept: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    suggested_followups: Optional[str] = None
    allow_mock_viva: bool = True
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 1
    due_date: Optional[datetime] = None
    visible_questions: List[AssignmentQuestionCreate] = []
    viva_questions: List[VivaQuestionCreate] = []


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    topic: Optional[str] = None
    concept: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    suggested_followups: Optional[str] = None
    is_active: Optional[bool] = None
    allow_mock_viva: Optional[bool] = None
    time_limit_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: str
    instructions: Optional[str] = None
    topic: Optional[str] = None
    concept: Optional[str] = None
    difficulty: DifficultyLevel
    suggested_followups: Optional[str] = None
    is_active: bool
    allow_mock_viva: bool
    time_limit_minutes: Optional[int] = None
    max_attempts: int
    due_date: Optional[datetime] = None
    teacher_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    visible_questions: List[AssignmentQuestionResponse] = []
    viva_questions: List[VivaQuestionResponse] = []

    class Config:
        from_attributes = True


class AssignmentSummary(BaseModel):
    id: int
    title: str
    description: str
    topic: Optional[str] = None
    difficulty: DifficultyLevel
    is_active: bool
    due_date: Optional[datetime] = None
    created_at: datetime
    question_count: int
    viva_question_count: int

    class Config:
        from_attributes = True
