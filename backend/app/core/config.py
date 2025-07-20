from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file with explicit path
env_path = Path(__file__).parent.parent.parent / ".env"
print(f"DEBUG: Current file: {__file__}")
print(f"DEBUG: Calculated .env path: {env_path}")
print(f"DEBUG: .env file exists: {env_path.exists()}")
print(f"DEBUG: Current working directory: {os.getcwd()}")

# Try loading from multiple possible locations
load_dotenv(dotenv_path=env_path)

# Also try loading from current directory as fallback
fallback_env = Path(".env")
print(f"DEBUG: Fallback .env path: {fallback_env.absolute()}")
print(f"DEBUG: Fallback .env exists: {fallback_env.exists()}")
load_dotenv(dotenv_path=fallback_env, override=False)

# Debug: Print to verify environment variables are loaded
print(f"DEBUG: DATABASE_USERNAME from env: {os.getenv('DATABASE_USERNAME', 'NOT_FOUND')}")
print(f"DEBUG: DATABASE_PASSWORD from env: {os.getenv('DATABASE_PASSWORD', 'NOT_FOUND')}")
print(f"DEBUG: All env vars starting with DATABASE_:")
for key, value in os.environ.items():
    if key.startswith('DATABASE_'):
        print(f"  {key}={value}")


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI-Powered Viva Assessment Platform"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database Configuration - Dynamic from .env
    DATABASE_USERNAME: str = os.getenv("DATABASE_USERNAME", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "password")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "assignchecker")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from individual components"""
        return f"postgresql://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_super_secret_jwt_key_here_change_in_production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Azure OpenAI Configuration - Dynamic from .env
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    # OAuth Configuration
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/auth/callback")
    
    # Media Storage Configuration
    MEDIA_STORAGE_PATH: str = os.getenv("MEDIA_STORAGE_PATH", "./media")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    ALLOWED_VIDEO_FORMATS: List[str] = ["mp4", "webm", "avi"]
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a"]
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "gif"]
    ALLOWED_DOCUMENT_FORMATS: List[str] = ["pdf", "doc", "docx", "txt"]
    
    # Whisper Configuration
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    
    # Viva Session Configuration
    DEFAULT_VIVA_DURATION_MINUTES: int = int(os.getenv("DEFAULT_VIVA_DURATION_MINUTES", "30"))
    MAX_VIVA_QUESTIONS: int = int(os.getenv("MAX_VIVA_QUESTIONS", "10"))
    MIN_VIVA_QUESTIONS: int = int(os.getenv("MIN_VIVA_QUESTIONS", "3"))
    
    # Security Configuration
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
