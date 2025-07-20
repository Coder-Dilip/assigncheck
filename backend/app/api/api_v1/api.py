from fastapi import APIRouter
from .endpoints import auth, users, assignments, submissions, viva, media

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(viva.router, prefix="/viva", tags=["viva"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
