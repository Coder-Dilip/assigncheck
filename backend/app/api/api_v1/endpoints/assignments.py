from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....models.user import User
from ....models.assignment import Assignment, AssignmentQuestion, VivaQuestion
from ....schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse, AssignmentSummary
)
from .auth import get_current_teacher, get_current_active_user

router = APIRouter()


@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new assignment (teachers only)"""
    # Create the assignment
    db_assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        instructions=assignment_data.instructions,
        topic=assignment_data.topic,
        concept=assignment_data.concept,
        difficulty=assignment_data.difficulty,
        suggested_followups=assignment_data.suggested_followups,
        allow_mock_viva=assignment_data.allow_mock_viva,
        time_limit_minutes=assignment_data.time_limit_minutes,
        max_attempts=assignment_data.max_attempts,
        due_date=assignment_data.due_date,
        teacher_id=current_user.id
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    # Add visible questions
    for question_data in assignment_data.visible_questions:
        db_question = AssignmentQuestion(
            assignment_id=db_assignment.id,
            question_text=question_data.question_text,
            question_type=question_data.question_type,
            order_index=question_data.order_index,
            points=question_data.points,
            is_required=question_data.is_required,
            options=question_data.options,
            correct_answer=question_data.correct_answer,
            hints=question_data.hints,
            explanation=question_data.explanation
        )
        db.add(db_question)
    
    # Add viva questions
    for viva_data in assignment_data.viva_questions:
        db_viva = VivaQuestion(
            assignment_id=db_assignment.id,
            question_text=viva_data.question_text,
            category=viva_data.category,
            difficulty=viva_data.difficulty,
            expected_keywords=viva_data.expected_keywords,
            follow_up_questions=viva_data.follow_up_questions,
            scoring_rubric=viva_data.scoring_rubric,
            is_adaptive=viva_data.is_adaptive,
            priority=viva_data.priority
        )
        db.add(db_viva)
    
    db.commit()
    db.refresh(db_assignment)
    
    return db_assignment


@router.get("/", response_model=List[AssignmentSummary])
def list_assignments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List assignments (teachers see their own, students see active ones)"""
    query = db.query(Assignment)
    
    if current_user.role.value == "teacher":
        # Teachers see their own assignments
        query = query.filter(Assignment.teacher_id == current_user.id)
    else:
        # Students see only active assignments
        query = query.filter(Assignment.is_active == True)
    
    assignments = query.offset(skip).limit(limit).all()
    
    # Convert to summary format with counts
    result = []
    for assignment in assignments:
        summary = AssignmentSummary(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            topic=assignment.topic,
            difficulty=assignment.difficulty,
            is_active=assignment.is_active,
            due_date=assignment.due_date,
            created_at=assignment.created_at,
            question_count=len(assignment.visible_questions),
            viva_question_count=len(assignment.viva_questions)
        )
        result.append(summary)
    
    return result


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get assignment details"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check permissions
    if current_user.role.value == "student" and not assignment.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assignment is not active"
        )
    
    if current_user.role.value == "teacher" and assignment.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this assignment"
        )
    
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update assignment (teachers only)"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this assignment"
        )
    
    # Update fields
    update_data = assignment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    
    return assignment


@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete assignment (teachers only)"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this assignment"
        )
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Assignment deleted successfully"}


@router.get("/{assignment_id}/viva-questions")
def get_viva_questions(
    assignment_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get viva questions for an assignment (teachers only - these are hidden from students)"""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view viva questions"
        )
    
    return assignment.viva_questions
