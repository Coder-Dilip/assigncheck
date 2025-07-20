from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.submission import SubmissionStatus


class SubmissionAnswerCreate(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_file_path: Optional[str] = None


class SubmissionAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: Optional[str] = None
    answer_file_path: Optional[str] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    teacher_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    assignment_id: int
    answers: List[SubmissionAnswerCreate]


class SubmissionUpdate(BaseModel):
    answers: Optional[List[SubmissionAnswerCreate]] = None
    status: Optional[SubmissionStatus] = None


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    status: SubmissionStatus
    attempt_number: int
    written_score: Optional[float] = None
    viva_score: Optional[float] = None
    total_score: Optional[float] = None
    max_possible_score: Optional[float] = None
    teacher_feedback: Optional[str] = None
    ai_feedback: Optional[str] = None
    teacher_override_score: Optional[float] = None
    created_at: datetime
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    answers: List[SubmissionAnswerResponse] = []

    class Config:
        from_attributes = True


class SubmissionSummary(BaseModel):
    id: int
    assignment_id: int
    assignment_title: str
    student_id: int
    student_name: str
    status: SubmissionStatus
    total_score: Optional[float] = None
    max_possible_score: Optional[float] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
