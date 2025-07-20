#!/usr/bin/env python3
"""
Script to create demo users for the AI-Powered Viva Assessment Platform
Run this script to populate the database with demo teacher and student accounts
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

def create_demo_users():
    """Create demo teacher and student users"""
    db: Session = SessionLocal()
    
    try:
        # Check if demo users already exist
        existing_teacher = db.query(User).filter(User.username == "teacher_demo").first()
        existing_student = db.query(User).filter(User.username == "student_demo").first()
        
        if existing_teacher and existing_student:
            print("Demo users already exist!")
            return
        
        # Create demo teacher
        if not existing_teacher:
            teacher_user = User(
                email="teacher@demo.com",
                username="teacher_demo",
                full_name="Demo Teacher",
                hashed_password=get_password_hash("password123"),
                role="teacher",
                bio="Demo teacher account for testing",
                is_active=True
            )
            db.add(teacher_user)
            print("Created demo teacher: username=teacher_demo, password=password123")
        
        # Create demo student
        if not existing_student:
            student_user = User(
                email="student@demo.com",
                username="student_demo", 
                full_name="Demo Student",
                hashed_password=get_password_hash("password123"),
                role="student",
                bio="Demo student account for testing",
                is_active=True
            )
            db.add(student_user)
            print("Created demo student: username=student_demo, password=password123")
        
        db.commit()
        print("\nDemo users created successfully!")
        print("You can now login with:")
        print("Teacher: username=teacher_demo, password=password123")
        print("Student: username=student_demo, password=password123")
        
    except Exception as e:
        print(f"Error creating demo users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating demo users for AI-Powered Viva Assessment Platform...")
    create_demo_users()
