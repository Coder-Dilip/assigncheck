from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....models.user import User
from ....models.media import MediaFile
from ....services.media_service import media_service
from .auth import get_current_active_user

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    viva_session_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload media file (video, audio, image, or document)"""
    
    try:
        # Save the uploaded file
        media_file = await media_service.save_upload(
            file=file,
            user_id=current_user.id,
            viva_session_id=viva_session_id
        )
        
        # Add to database
        db.add(media_file)
        db.commit()
        db.refresh(media_file)
        
        # Schedule background processing
        if media_file.media_type.value in ["video", "audio"]:
            background_tasks.add_task(process_media_file, media_file.id, db)
        
        return {
            "message": "File uploaded successfully",
            "file_id": media_file.id,
            "filename": media_file.filename,
            "media_type": media_file.media_type.value,
            "file_url": media_service.get_file_url(media_file),
            "processing_status": media_file.processing_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


async def process_media_file(file_id: int, db: Session):
    """Background task to process media files (transcription, compression)"""
    media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    if not media_file:
        return
    
    try:
        media_file.processing_status = "processing"
        db.commit()
        
        # Transcribe audio/video files
        if media_file.media_type.value in ["video", "audio"]:
            transcript = await media_service.transcribe_audio(media_file)
            if transcript:
                print(f"Transcription completed for file {media_file.id}")
        
        # Compress video files
        if media_file.media_type.value == "video":
            compressed = await media_service.compress_video(media_file)
            if compressed:
                print(f"Compression completed for file {media_file.id}")
        
        db.commit()
        
    except Exception as e:
        print(f"Media processing failed for file {file_id}: {e}")
        media_file.processing_status = "failed"
        db.commit()


@router.get("/", response_model=List[dict])
def list_media_files(
    viva_session_id: int = None,
    media_type: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List media files for current user"""
    query = db.query(MediaFile).filter(MediaFile.uploaded_by_id == current_user.id)
    
    if viva_session_id:
        query = query.filter(MediaFile.viva_session_id == viva_session_id)
    
    if media_type:
        query = query.filter(MediaFile.media_type == media_type)
    
    media_files = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": mf.id,
            "filename": mf.filename,
            "original_filename": mf.original_filename,
            "media_type": mf.media_type.value,
            "file_size": mf.file_size,
            "duration_seconds": mf.duration_seconds,
            "processing_status": mf.processing_status,
            "file_url": media_service.get_file_url(mf),
            "created_at": mf.created_at,
            "viva_session_id": mf.viva_session_id
        }
        for mf in media_files
    ]


@router.get("/{file_id}", response_model=dict)
def get_media_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get media file details"""
    media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Check permissions - users can only access their own files
    # Teachers can access files from their students' viva sessions
    if current_user.role.value == "student":
        if media_file.uploaded_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
    elif current_user.role.value == "teacher":
        # Check if file belongs to a viva session for teacher's assignment
        if media_file.viva_session_id:
            from ....models.viva_session import VivaSession
            from ....models.submission import Submission
            from ....models.assignment import Assignment
            
            viva_session = db.query(VivaSession).filter(VivaSession.id == media_file.viva_session_id).first()
            if viva_session:
                submission = db.query(Submission).filter(Submission.id == viva_session.submission_id).first()
                if submission:
                    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
                    if assignment and assignment.teacher_id != current_user.id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to access this file"
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to access this file"
                    )
        elif media_file.uploaded_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file"
            )
    
    return {
        "id": media_file.id,
        "filename": media_file.filename,
        "original_filename": media_file.original_filename,
        "media_type": media_file.media_type.value,
        "file_size": media_file.file_size,
        "mime_type": media_file.mime_type,
        "duration_seconds": media_file.duration_seconds,
        "width": media_file.width,
        "height": media_file.height,
        "processing_status": media_file.processing_status,
        "file_url": media_service.get_file_url(media_file),
        "created_at": media_file.created_at,
        "viva_session_id": media_file.viva_session_id
    }


@router.get("/{file_id}/transcript")
def get_transcript(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transcript for audio/video file"""
    media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Check permissions (same as get_media_file)
    if current_user.role.value == "student" and media_file.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this file"
        )
    
    if not media_file.transcript_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not available for this file"
        )
    
    try:
        from pathlib import Path
        transcript_path = Path(media_service.storage_path) / media_file.transcript_file_path
        
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()
        
        return {
            "file_id": file_id,
            "transcript": transcript_text,
            "processing_status": media_file.processing_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read transcript"
        )


@router.delete("/{file_id}")
def delete_media_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete media file"""
    media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )
    
    # Only file owner can delete
    if media_file.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this file"
        )
    
    # Delete physical file
    success = media_service.delete_file(media_file)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file from storage"
        )
    
    # Delete database record
    db.delete(media_file)
    db.commit()
    
    return {"message": "File deleted successfully"}
