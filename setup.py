#!/usr/bin/env python3
"""
Setup script for AI-Powered Viva Assessment Platform
This script helps initialize the development environment
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    requirements = {
        'python': 'python --version',
        'node': 'node --version',
        'npm': 'npm --version',
        'docker': 'docker --version',
        'docker-compose': 'docker-compose --version'
    }
    
    missing = []
    for tool, command in requirements.items():
        result = run_command(command)
        if result:
            print(f"✅ {tool}: {result.strip()}")
        else:
            print(f"❌ {tool}: Not found")
            missing.append(tool)
    
    if missing:
        print(f"\n⚠️  Missing requirements: {', '.join(missing)}")
        print("Please install the missing tools before continuing.")
        return False
    
    return True

def setup_environment():
    """Set up environment files"""
    print("\n🔧 Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("Creating .env file...")
        with open('.env.example', 'r') as example:
            content = example.read()
        
        with open('.env', 'w') as env:
            env.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please update the .env file with your Azure OpenAI credentials")
    else:
        print("✅ .env file already exists")

def setup_backend():
    """Set up Python backend"""
    print("\n🐍 Setting up Python backend...")
    
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment
    venv_path = backend_dir / 'venv'
    if not venv_path.exists():
        print("Creating virtual environment...")
        run_command('python -m venv venv', cwd=backend_dir)
    
    # Install requirements
    print("Installing Python dependencies...")
    if os.name == 'nt':  # Windows
        pip_cmd = 'venv\\Scripts\\pip install -r requirements.txt'
    else:  # Unix/Linux/Mac
        pip_cmd = 'venv/bin/pip install -r requirements.txt'
    
    result = run_command(pip_cmd, cwd=backend_dir)
    if result is not None:
        print("✅ Python dependencies installed")
        return True
    else:
        print("❌ Failed to install Python dependencies")
        return False

def setup_frontend():
    """Set up React frontend"""
    print("\n⚛️  Setting up React frontend...")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install npm dependencies
    print("Installing Node.js dependencies...")
    result = run_command('npm install', cwd=frontend_dir)
    if result is not None:
        print("✅ Node.js dependencies installed")
        return True
    else:
        print("❌ Failed to install Node.js dependencies")
        return False

def create_database_init():
    """Create database initialization script"""
    print("\n🗄️  Creating database initialization...")
    
    init_sql = """
-- Initialize database for AI-Powered Viva Assessment Platform
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create demo users
INSERT INTO users (email, username, full_name, hashed_password, role, is_active, is_verified) VALUES
('teacher@demo.com', 'teacher_demo', 'Demo Teacher', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq9w5KS', 'teacher', true, true),
('student@demo.com', 'student_demo', 'Demo Student', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq9w5KS', 'student', true, true)
ON CONFLICT (email) DO NOTHING;
"""
    
    with open('init.sql', 'w') as f:
        f.write(init_sql)
    
    print("✅ Database initialization script created")

def main():
    """Main setup function"""
    print("🚀 AI-Powered Viva Assessment Platform Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Create database init
    create_database_init()
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update the .env file with your Azure OpenAI credentials")
    print("2. Run 'docker-compose up' to start the development environment")
    print("3. Visit http://localhost:3000 to access the application")
    print("\nDemo credentials:")
    print("- Teacher: teacher@demo.com / password123")
    print("- Student: student@demo.com / password123")

if __name__ == "__main__":
    main()
