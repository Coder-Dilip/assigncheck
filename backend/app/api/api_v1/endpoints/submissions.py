from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....models.user import User
from ....models.assignment import Assignment
from ....models.submission import Submission, SubmissionAnswer, SubmissionStatus
from ....schemas.submission import (
    SubmissionCreate, SubmissionUpdate, SubmissionResponse, SubmissionSummary
)
from .auth import get_current_active_user, get_current_student, get_current_teacher

router = APIRouter()


@router.post("/", response_model=SubmissionResponse)
def create_submission(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Create a new submission (students only)"""
    # Check if assignment exists and is active
    assignment = db.query(Assignment).filter(Assignment.id == submission_data.assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if not assignment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment is not active"
        )
    
    # Check if student has already reached max attempts
    existing_submissions = db.query(Submission).filter(
        Submission.assignment_id == submission_data.assignment_id,
        Submission.student_id == current_user.id
    ).count()
    
    if existing_submissions >= assignment.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum attempts reached for this assignment"
        )
    
    # Create submission
    db_submission = Submission(
        assignment_id=submission_data.assignment_id,
        student_id=current_user.id,
        attempt_number=existing_submissions + 1,
        status=SubmissionStatus.DRAFT
    )
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # Add answers
    for answer_data in submission_data.answers:
        db_answer = SubmissionAnswer(
            submission_id=db_submission.id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            answer_file_path=answer_data.answer_file_path
        )
        db.add(db_answer)
    
    db.commit()
    db.refresh(db_submission)
    
    return db_submission


@router.get("/", response_model=List[SubmissionSummary])
def list_submissions(
    assignment_id: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List submissions"""
    query = db.query(Submission)
    
    if current_user.role.value == "student":
        # Students see only their own submissions
        query = query.filter(Submission.student_id == current_user.id)
    elif current_user.role.value == "teacher":
        # Teachers see submissions for their assignments
        if assignment_id:
            # Check if teacher owns the assignment
            assignment = db.query(Assignment).filter(
                Assignment.id == assignment_id,
                Assignment.teacher_id == current_user.id
            ).first()
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view submissions for this assignment"
                )
            query = query.filter(Submission.assignment_id == assignment_id)
        else:
            # Get all submissions for teacher's assignments
            teacher_assignments = db.query(Assignment.id).filter(
                Assignment.teacher_id == current_user.id
            ).subquery()
            query = query.filter(Submission.assignment_id.in_(teacher_assignments))
    
    submissions = query.offset(skip).limit(limit).all()
    
    # Convert to summary format
    result = []
    for submission in submissions:
        summary = SubmissionSummary(
            id=submission.id,
            assignment_id=submission.assignment_id,
            assignment_title=submission.assignment.title,
            student_id=submission.student_id,
            student_name=submission.student.full_name,
            status=submission.status,
            total_score=submission.total_score,
            max_possible_score=submission.max_possible_score,
            submitted_at=submission.submitted_at,
            graded_at=submission.graded_at
        )
        result.append(summary)
    
    return result


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get submission details"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check permissions
    if current_user.role.value == "student" and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )
    elif current_user.role.value == "teacher" and submission.assignment.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )
    
    return submission


@router.put("/{submission_id}", response_model=SubmissionResponse)
def update_submission(
    submission_id: int,
    submission_data: SubmissionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update submission"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check permissions
    if current_user.role.value == "student":
        if submission.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this submission"
            )
        if submission.status != SubmissionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update draft submissions"
            )
    elif current_user.role.value == "teacher":
        if submission.assignment.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this submission"
            )
    
    # Update submission
    if submission_data.status:
        submission.status = submission_data.status
        if submission_data.status == SubmissionStatus.SUBMITTED:
            from datetime import datetime
            submission.submitted_at = datetime.utcnow()
    
    # Update answers if provided
    if submission_data.answers:
        # Remove existing answers
        db.query(SubmissionAnswer).filter(
            SubmissionAnswer.submission_id == submission_id
        ).delete()
        
        # Add new answers
        for answer_data in submission_data.answers:
            db_answer = SubmissionAnswer(
                submission_id=submission_id,
                question_id=answer_data.question_id,
                answer_text=answer_data.answer_text,
                answer_file_path=answer_data.answer_file_path
            )
            db.add(db_answer)
    
    db.commit()
    db.refresh(submission)
    
    return submission


@router.post("/{submission_id}/submit")
def submit_submission(
    submission_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit a draft submission for grading"""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this submission"
        )
    
    if submission.status != SubmissionStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only submit draft submissions"
        )
    
    # Update status and timestamp
    from datetime import datetime
    submission.status = SubmissionStatus.SUBMITTED
    submission.submitted_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Submission submitted successfully", "submission_id": submission_id}
