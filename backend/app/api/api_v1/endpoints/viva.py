from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....models.user import User
from ....models.submission import Submission
from ....models.viva_session import VivaSession, VivaResponse, VivaSessionType, VivaSessionStatus
from ....models.assignment import Assignment
from ....schemas.viva import (
    VivaSessionCreate, VivaSessionUpdate, VivaSessionResponse,
    VivaResponseCreate, MockVivaRequest, AIQuestionRequest
)
from ....services.ai_service import ai_service
from .auth import get_current_active_user, get_current_student, get_current_teacher

router = APIRouter()


@router.post("/sessions", response_model=VivaSessionResponse)
async def create_viva_session(
    session_data: VivaSessionCreate,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Create a new viva session (students only)"""
    # Check if submission exists and belongs to student
    submission = db.query(Submission).filter(Submission.id == session_data.submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    if submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create viva session for this submission"
        )
    
    # Check if submission is submitted (can't do viva on draft)
    if submission.status.value == "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create viva session for draft submission"
        )
    
    # For final viva, check if mock viva is required/recommended
    if session_data.session_type == VivaSessionType.FINAL:
        existing_mock = db.query(VivaSession).filter(
            VivaSession.submission_id == session_data.submission_id,
            VivaSession.session_type == VivaSessionType.MOCK,
            VivaSession.status == VivaSessionStatus.COMPLETED
        ).first()
        
        if not existing_mock and submission.assignment.allow_mock_viva:
            # Recommend mock viva first (but don't enforce)
            pass
    
    # Create viva session
    db_session = VivaSession(
        submission_id=session_data.submission_id,
        student_id=current_user.id,
        session_type=session_data.session_type,
        status=VivaSessionStatus.SCHEDULED
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/sessions", response_model=List[VivaSessionResponse])
def list_viva_sessions(
    submission_id: int = None,
    session_type: VivaSessionType = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List viva sessions"""
    query = db.query(VivaSession)
    
    if current_user.role.value == "student":
        query = query.filter(VivaSession.student_id == current_user.id)
    elif current_user.role.value == "teacher":
        # Teachers see sessions for their assignments
        teacher_submissions = db.query(Submission.id).join(Assignment).filter(
            Assignment.teacher_id == current_user.id
        ).subquery()
        query = query.filter(VivaSession.submission_id.in_(teacher_submissions))
    
    if submission_id:
        query = query.filter(VivaSession.submission_id == submission_id)
    
    if session_type:
        query = query.filter(VivaSession.session_type == session_type)
    
    return query.all()


@router.get("/sessions/{session_id}", response_model=VivaSessionResponse)
def get_viva_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get viva session details"""
    session = db.query(VivaSession).filter(VivaSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viva session not found"
        )
    
    # Check permissions
    if current_user.role.value == "student" and session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this viva session"
        )
    elif current_user.role.value == "teacher":
        submission = db.query(Submission).filter(Submission.id == session.submission_id).first()
        if submission.assignment.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this viva session"
            )
    
    return session


@router.put("/sessions/{session_id}", response_model=VivaSessionResponse)
def update_viva_session(
    session_id: int,
    session_data: VivaSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update viva session"""
    session = db.query(VivaSession).filter(VivaSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viva session not found"
        )
    
    # Check permissions
    if current_user.role.value == "student" and session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this viva session"
        )
    
    # Update fields
    update_data = session_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    # Update timestamps based on status
    if session_data.status:
        from datetime import datetime
        if session_data.status == VivaSessionStatus.IN_PROGRESS and not session.started_at:
            session.started_at = datetime.utcnow()
        elif session_data.status == VivaSessionStatus.COMPLETED and not session.completed_at:
            session.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/sessions/{session_id}/start")
async def start_viva_session(
    session_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Start a viva session and get the first AI-generated question"""
    session = db.query(VivaSession).filter(VivaSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viva session not found"
        )
    
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to start this viva session"
        )
    
    if session.status != VivaSessionStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in scheduled state"
        )
    
    # Update session status
    from datetime import datetime
    session.status = VivaSessionStatus.IN_PROGRESS
    session.started_at = datetime.utcnow()
    
    # Get assignment and submission context for AI
    submission = db.query(Submission).filter(Submission.id == session.submission_id).first()
    assignment = submission.assignment
    
    # Prepare context for AI
    assignment_context = f"Title: {assignment.title}\nDescription: {assignment.description}"
    if assignment.topic:
        assignment_context += f"\nTopic: {assignment.topic}"
    if assignment.concept:
        assignment_context += f"\nConcept: {assignment.concept}"
    
    # Get student's written answers
    student_answers = ""
    for answer in submission.answers:
        student_answers += f"Q: {answer.question.question_text}\nA: {answer.answer_text}\n\n"
    
    # Generate first question
    ai_request = AIQuestionRequest(
        assignment_context=assignment_context,
        student_answers=student_answers,
        difficulty_level=assignment.difficulty.value,
        question_type="conceptual"
    )
    
    try:
        ai_response = await ai_service.generate_viva_question(ai_request)
        
        # Create first viva response record
        viva_response = VivaResponse(
            viva_session_id=session.id,
            question_text=ai_response.question,
            order_index=1
        )
        
        db.add(viva_response)
        session.questions_asked = 1
        
        db.commit()
        db.refresh(session)
        
        return {
            "message": "Viva session started",
            "session_id": session.id,
            "first_question": ai_response.question,
            "response_id": viva_response.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate first question"
        )


@router.post("/sessions/{session_id}/respond")
async def submit_viva_response(
    session_id: int,
    response_data: VivaResponseCreate,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit a response to a viva question and get the next question"""
    session = db.query(VivaSession).filter(VivaSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viva session not found"
        )
    
    if session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to respond in this viva session"
        )
    
    if session.status != VivaSessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress"
        )
    
    # Find the current question to respond to
    current_response = db.query(VivaResponse).filter(
        VivaResponse.viva_session_id == session_id,
        VivaResponse.response_text.is_(None)
    ).order_by(VivaResponse.order_index.desc()).first()
    
    if not current_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending question to respond to"
        )
    
    # Update the response
    current_response.response_text = response_data.response_text
    current_response.response_audio_path = response_data.response_audio_path
    current_response.response_timestamp = response_data.response_timestamp
    current_response.response_duration = response_data.response_duration
    
    session.questions_answered += 1
    
    # Evaluate the response using AI
    try:
        # Get expected keywords and scoring criteria (would be stored from question generation)
        evaluation = await ai_service.evaluate_viva_response(
            question=current_response.question_text,
            response=response_data.response_text or "",
            expected_keywords=[],  # Would be stored from question generation
            scoring_criteria={}    # Would be stored from question generation
        )
        
        # Update response with AI evaluation
        current_response.confidence_score = evaluation.get("confidence_score")
        current_response.accuracy_score = evaluation.get("accuracy_score")
        current_response.completeness_score = evaluation.get("completeness_score")
        current_response.ai_feedback = evaluation.get("feedback")
        current_response.score = evaluation.get("overall_score", 0) * 10  # Convert to 10-point scale
        current_response.max_score = 10
        
    except Exception as e:
        # Continue without AI evaluation if it fails
        current_response.score = 7  # Default score
        current_response.max_score = 10
    
    db.commit()
    
    # Check if we should ask another question (limit to 5-7 questions typically)
    if session.questions_asked < 5:  # Configurable limit
        # Generate next question based on previous responses
        try:
            submission = db.query(Submission).filter(Submission.id == session.submission_id).first()
            assignment = submission.assignment
            
            # Get previous responses for context
            previous_responses = [r.response_text for r in session.responses if r.response_text]
            
            assignment_context = f"Title: {assignment.title}\nDescription: {assignment.description}"
            student_answers = ""
            for answer in submission.answers:
                student_answers += f"Q: {answer.question.question_text}\nA: {answer.answer_text}\n\n"
            
            ai_request = AIQuestionRequest(
                assignment_context=assignment_context,
                student_answers=student_answers,
                previous_responses=previous_responses,
                difficulty_level=assignment.difficulty.value,
                question_type="application"  # Vary question types
            )
            
            ai_response = await ai_service.generate_viva_question(ai_request)
            
            # Create next question
            next_response = VivaResponse(
                viva_session_id=session.id,
                question_text=ai_response.question,
                order_index=session.questions_asked + 1
            )
            
            db.add(next_response)
            session.questions_asked += 1
            db.commit()
            
            return {
                "message": "Response recorded",
                "next_question": ai_response.question,
                "response_id": next_response.id,
                "session_complete": False
            }
            
        except Exception as e:
            # End session if question generation fails
            pass
    
    # End the session
    from datetime import datetime
    session.status = VivaSessionStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    
    # Calculate overall scores
    total_score = sum(r.score or 0 for r in session.responses if r.score)
    max_possible = sum(r.max_score or 0 for r in session.responses if r.max_score)
    
    session.total_score = total_score
    session.max_possible_score = max_possible
    
    if session.responses:
        session.overall_confidence_score = sum(r.confidence_score or 0 for r in session.responses) / len(session.responses)
        session.communication_score = sum(r.confidence_score or 0 for r in session.responses) / len(session.responses)
        session.technical_accuracy_score = sum(r.accuracy_score or 0 for r in session.responses) / len(session.responses)
    
    db.commit()
    
    return {
        "message": "Viva session completed",
        "session_complete": True,
        "total_score": total_score,
        "max_possible_score": max_possible
    }


@router.post("/mock-questions", response_model=List[dict])
async def generate_mock_questions(
    request: MockVivaRequest,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate mock viva questions for practice"""
    assignment = db.query(Assignment).filter(Assignment.id == request.assignment_id).first()
    
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
    
    # Prepare assignment context
    assignment_context = f"Title: {assignment.title}\nDescription: {assignment.description}"
    if assignment.topic:
        assignment_context += f"\nTopic: {assignment.topic}"
    if assignment.concept:
        assignment_context += f"\nConcept: {assignment.concept}"
    
    try:
        mock_questions = await ai_service.generate_mock_questions(
            assignment_context=assignment_context,
            difficulty_preference=request.difficulty_preference,
            question_count=request.question_count
        )
        
        return [
            {
                "question": q.question,
                "expected_keywords": q.expected_keywords,
                "follow_up_questions": q.follow_up_questions,
                "scoring_criteria": q.scoring_criteria
            }
            for q in mock_questions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mock questions"
        )
