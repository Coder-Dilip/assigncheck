# AI-Powered Viva Assessment Platform

An open-source educational platform that combines traditional written assessments with AI-enhanced oral evaluation (viva interviews).

## Overview

This platform enables teachers to create comprehensive assessments with both written and oral components. Students complete written assignments and then participate in AI-conducted camera-based viva interviews for deeper evaluation.

## Key Features

### For Teachers
- Create assignments with visible questions and hidden viva questions
- Review student submissions and AI-evaluated viva sessions
- Override AI scores and provide additional feedback
- Access detailed performance analytics

### For Students
- Submit written assignment solutions
- Participate in AI-conducted viva interviews
- Practice with mock viva sessions
- Receive comprehensive feedback on both written and oral performance

### AI-Powered Features
- Adaptive questioning based on student responses
- Real-time speech-to-text transcription
- Intelligent scoring and feedback generation
- Mock interview question generation

## Technology Stack

### Frontend
- **React.js** with modern hooks and components
- **Tailwind CSS** for responsive, utility-first styling
- **Vite** for fast development and building

### Backend
- **FastAPI** (Python) for high-performance API
- **SQLAlchemy** for database ORM
- **PostgreSQL** for data persistence
- **Pydantic** for data validation

### AI/ML Integration
- **Azure OpenAI** for intelligent questioning and evaluation
- **Whisper** for speech-to-text transcription
- **OpenCV** for video processing

### Media Management
- **FFmpeg** for video/audio compression and transcoding
- Local file system with efficient chunking
- Open-source media handling (no cloud dependencies)

### Authentication
- **OAuth 2.0** integration
- **JWT** tokens for session management

## Project Structure

```
assignchecker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   ├── package.json
│   └── vite.config.js
├── media/                  # Local media storage
├── docs/                   # Documentation
└── docker-compose.yml      # Development environment
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- FFmpeg

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd assignchecker
```

2. Set up the backend
```bash
cd backend
pip install -r requirements.txt
```

3. Set up the frontend
```bash
cd frontend
npm install
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the development servers
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/assignchecker

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint

# Authentication
JWT_SECRET_KEY=your_secret_key
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret

# Media Storage
MEDIA_STORAGE_PATH=./media
MAX_FILE_SIZE=100MB
```

## Contributing

This project is fully open-source and welcomes contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Philosophy

This platform is built with transparency, educational freedom, and community collaboration in mind. All components (except external AI services) are open-source and auditable.
