from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....models.user import User, UserRole
from ....schemas.user import UserUpdate, UserProfile
from ....schemas.auth import UserResponse
from .auth import get_current_active_user, get_current_teacher

router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's detailed profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/", response_model=List[UserResponse])
def list_users(
    role: UserRole = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List users (teachers can see students, students can see teachers)"""
    query = db.query(User).filter(User.is_active == True)
    
    if current_user.role == UserRole.TEACHER:
        # Teachers can see all students and other teachers
        if role:
            query = query.filter(User.role == role)
    elif current_user.role == UserRole.STUDENT:
        # Students can only see teachers
        query = query.filter(User.role == UserRole.TEACHER)
    else:
        # Admin can see all users
        if role:
            query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserProfile)
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user profile by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.STUDENT:
        # Students can only view teacher profiles and their own
        if user.role != UserRole.TEACHER and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this profile"
            )
    elif current_user.role == UserRole.TEACHER:
        # Teachers can view student profiles and other teacher profiles
        if user.role not in [UserRole.STUDENT, UserRole.TEACHER] and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this profile"
            )
    
    return user


@router.get("/students/my-students", response_model=List[UserResponse])
def get_my_students(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students who have submitted assignments to this teacher"""
    from ....models.assignment import Assignment
    from ....models.submission import Submission
    
    # Get students who have submitted to teacher's assignments
    students = (
        db.query(User)
        .join(Submission, User.id == Submission.student_id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Assignment.teacher_id == current_user.id)
        .filter(User.is_active == True)
        .distinct()
        .all()
    )
    
    return students


@router.get("/teachers/my-teachers", response_model=List[UserResponse])
def get_my_teachers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get teachers whose assignments this student has access to"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    from ....models.assignment import Assignment
    
    # Get teachers who have active assignments
    teachers = (
        db.query(User)
        .join(Assignment, User.id == Assignment.teacher_id)
        .filter(Assignment.is_active == True)
        .filter(User.is_active == True)
        .distinct()
        .all()
    )
    
    return teachers


@router.get("/stats/dashboard")
def get_user_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    
    if current_user.role == UserRole.TEACHER:
        from ....models.assignment import Assignment
        from ....models.submission import Submission
        from ....models.viva_session import VivaSession
        
        # Teacher dashboard stats
        total_assignments = db.query(Assignment).filter(Assignment.teacher_id == current_user.id).count()
        active_assignments = db.query(Assignment).filter(
            Assignment.teacher_id == current_user.id,
            Assignment.is_active == True
        ).count()
        
        total_submissions = (
            db.query(Submission)
            .join(Assignment)
            .filter(Assignment.teacher_id == current_user.id)
            .count()
        )
        
        pending_reviews = (
            db.query(Submission)
            .join(Assignment)
            .filter(Assignment.teacher_id == current_user.id)
            .filter(Submission.status.in_(["submitted", "under_review"]))
            .count()
        )
        
        completed_vivas = (
            db.query(VivaSession)
            .join(Submission)
            .join(Assignment)
            .filter(Assignment.teacher_id == current_user.id)
            .filter(VivaSession.status == "completed")
            .count()
        )
        
        return {
            "role": "teacher",
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
            "total_submissions": total_submissions,
            "pending_reviews": pending_reviews,
            "completed_vivas": completed_vivas
        }
    
    elif current_user.role == UserRole.STUDENT:
        from ....models.submission import Submission
        from ....models.viva_session import VivaSession
        
        # Student dashboard stats
        total_submissions = db.query(Submission).filter(Submission.student_id == current_user.id).count()
        
        completed_submissions = db.query(Submission).filter(
            Submission.student_id == current_user.id,
            Submission.status == "submitted"
        ).count()
        
        graded_submissions = db.query(Submission).filter(
            Submission.student_id == current_user.id,
            Submission.status == "graded"
        ).count()
        
        completed_vivas = db.query(VivaSession).filter(
            VivaSession.student_id == current_user.id,
            VivaSession.status == "completed"
        ).count()
        
        mock_vivas = db.query(VivaSession).filter(
            VivaSession.student_id == current_user.id,
            VivaSession.session_type == "mock",
            VivaSession.status == "completed"
        ).count()
        
        # Calculate average score
        avg_score = db.query(Submission).filter(
            Submission.student_id == current_user.id,
            Submission.total_score.isnot(None)
        ).with_entities(
            db.func.avg(Submission.total_score)
        ).scalar()
        
        return {
            "role": "student",
            "total_submissions": total_submissions,
            "completed_submissions": completed_submissions,
            "graded_submissions": graded_submissions,
            "completed_vivas": completed_vivas,
            "mock_vivas": mock_vivas,
            "average_score": round(avg_score, 2) if avg_score else None
        }
    
    else:
        return {"role": current_user.role.value, "message": "Dashboard not implemented for this role"}
