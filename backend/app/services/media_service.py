import os
import uuid
import shutil
import ffmpeg
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from ..core.config import settings
from ..models.media import MediaFile, MediaType

# Try to import whisper with error handling for Windows compatibility
try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception as e:
    print(f"Warning: Whisper not available - {e}")
    WHISPER_AVAILABLE = False
    whisper = None


class MediaService:
    def __init__(self):
        self.storage_path = Path(settings.MEDIA_STORAGE_PATH)
        self.storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "videos").mkdir(exist_ok=True)
        (self.storage_path / "audio").mkdir(exist_ok=True)
        (self.storage_path / "images").mkdir(exist_ok=True)
        (self.storage_path / "documents").mkdir(exist_ok=True)
        (self.storage_path / "transcripts").mkdir(exist_ok=True)
        
        # Load Whisper model for transcription
        try:
            if WHISPER_AVAILABLE:
                self.whisper_model = whisper.load_model(settings.WHISPER_MODEL)
            else:
                self.whisper_model = None
        except Exception as e:
            print(f"Warning: Could not load Whisper model: {e}")
            self.whisper_model = None

    def _get_media_type(self, mime_type: str) -> MediaType:
        """Determine media type from MIME type"""
        if mime_type.startswith("video/"):
            return MediaType.VIDEO
        elif mime_type.startswith("audio/"):
            return MediaType.AUDIO
        elif mime_type.startswith("image/"):
            return MediaType.IMAGE
        else:
            return MediaType.DOCUMENT

    def _generate_filename(self, original_filename: str, media_type: MediaType) -> str:
        """Generate unique filename"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"

    def _get_storage_subdir(self, media_type: MediaType) -> str:
        """Get storage subdirectory for media type"""
        type_map = {
            MediaType.VIDEO: "videos",
            MediaType.AUDIO: "audio", 
            MediaType.IMAGE: "images",
            MediaType.DOCUMENT: "documents"
        }
        return type_map.get(media_type, "documents")

    async def save_upload(
        self, 
        file: UploadFile, 
        user_id: int,
        viva_session_id: Optional[int] = None
    ) -> MediaFile:
        """Save uploaded file and create database record"""
        
        # Validate file size
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        file_size = 0
        
        # Read file content to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Determine media type
        media_type = self._get_media_type(file.content_type or "")
        
        # Validate file type
        file_extension = Path(file.filename or "").suffix.lower().lstrip('.')
        if media_type == MediaType.VIDEO and file_extension not in settings.ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Video format not allowed. Allowed formats: {settings.ALLOWED_VIDEO_FORMATS}"
            )
        elif media_type == MediaType.AUDIO and file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Audio format not allowed. Allowed formats: {settings.ALLOWED_AUDIO_FORMATS}"
            )
        
        # Generate unique filename and path
        filename = self._generate_filename(file.filename or "upload", media_type)
        subdir = self._get_storage_subdir(media_type)
        file_path = self.storage_path / subdir / filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Get file metadata
        duration_seconds = None
        width = None
        height = None
        
        if media_type in [MediaType.VIDEO, MediaType.AUDIO]:
            try:
                probe = ffmpeg.probe(str(file_path))
                duration_seconds = int(float(probe['format']['duration']))
                
                if media_type == MediaType.VIDEO:
                    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                    if video_stream:
                        width = video_stream.get('width')
                        height = video_stream.get('height')
            except Exception as e:
                print(f"Warning: Could not get media metadata: {e}")
        
        # Create database record
        media_file = MediaFile(
            filename=filename,
            original_filename=file.filename or "upload",
            file_path=str(file_path.relative_to(self.storage_path)),
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            media_type=media_type,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            uploaded_by_id=user_id,
            viva_session_id=viva_session_id,
            processing_status="pending"
        )
        
        return media_file

    async def transcribe_audio(self, media_file: MediaFile) -> Optional[str]:
        """Transcribe audio file using Whisper"""
        if not WHISPER_AVAILABLE:
            return None
        
        if media_file.media_type not in [MediaType.AUDIO, MediaType.VIDEO]:
            return None
        
        try:
            file_path = self.storage_path / media_file.file_path
            
            # For video files, extract audio first
            if media_file.media_type == MediaType.VIDEO:
                audio_path = self.storage_path / "audio" / f"{Path(media_file.filename).stem}.wav"
                ffmpeg.input(str(file_path)).output(str(audio_path)).run(overwrite_output=True, quiet=True)
                transcribe_path = audio_path
            else:
                transcribe_path = file_path
            
            # Transcribe using Whisper
            result = self.whisper_model.transcribe(str(transcribe_path))
            transcript_text = result["text"]
            
            # Save transcript to file
            transcript_filename = f"{Path(media_file.filename).stem}_transcript.txt"
            transcript_path = self.storage_path / "transcripts" / transcript_filename
            
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            
            # Update media file record
            media_file.transcript_file_path = str(transcript_path.relative_to(self.storage_path))
            media_file.processing_status = "completed"
            
            return transcript_text
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            media_file.processing_status = "failed"
            return None

    async def compress_video(self, media_file: MediaFile) -> bool:
        """Compress video file for storage efficiency"""
        if media_file.media_type != MediaType.VIDEO:
            return False
        
        try:
            input_path = self.storage_path / media_file.file_path
            output_filename = f"compressed_{media_file.filename}"
            output_path = self.storage_path / "videos" / output_filename
            
            # Compress video using ffmpeg
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    vcodec='libx264',
                    crf=23,
                    preset='medium',
                    acodec='aac',
                    audio_bitrate='128k'
                )
                .run(overwrite_output=True, quiet=True)
            )
            
            # Replace original with compressed version
            os.remove(input_path)
            shutil.move(output_path, input_path)
            
            # Update file size
            media_file.file_size = os.path.getsize(input_path)
            media_file.processing_status = "completed"
            
            return True
            
        except Exception as e:
            print(f"Video compression failed: {e}")
            media_file.processing_status = "failed"
            return False

    def delete_file(self, media_file: MediaFile) -> bool:
        """Delete media file and associated files"""
        try:
            # Delete main file
            main_path = self.storage_path / media_file.file_path
            if main_path.exists():
                os.remove(main_path)
            
            # Delete transcript if exists
            if media_file.transcript_file_path:
                transcript_path = self.storage_path / media_file.transcript_file_path
                if transcript_path.exists():
                    os.remove(transcript_path)
            
            return True
            
        except Exception as e:
            print(f"File deletion failed: {e}")
            return False

    def get_file_url(self, media_file: MediaFile) -> str:
        """Get URL for accessing media file"""
        return f"/media/{media_file.file_path}"


# Global media service instance
media_service = MediaService()
