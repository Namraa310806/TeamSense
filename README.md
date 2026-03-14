# TeamSense — AI HR Intelligence Platform

An AI-powered organizational memory system for HR teams. Ingest employee meeting transcripts, analyze sentiment, extract insights, and query employee history using RAG.

## 🏗️ Architecture

```text
User → React Dashboard → Django REST API → AI Processing Layer → PostgreSQL + PGVector
                                         → Celery Workers (Redis)
```

## 🚀 Quick Start

### Traditional Local Run (No Docker)

This is the fastest development path when Docker builds are slow.

Prerequisites:

- Python 3.10+
- Node.js 18+
- ffmpeg available on PATH (required for meeting recording upload)

Step 1: Create local env file.

```bash
copy .env.local.example .env
```

Step 2: Install backend dependencies.

```bash
cd backend
pip install -r requirements.txt
```

Step 3: Run terminals (3-4 terminals).

Terminal 1 (backend API):

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Terminal 2 (frontend):

```bash
cd frontend
npm install
npm run dev
```

Terminal 3 (seed demo data once):

```bash
cd backend
python manage.py seed_data
```

Terminal 4 (optional celery worker):

```bash
cd backend
celery -A teamsense worker -l info
```

Notes:

- With `CELERY_TASK_ALWAYS_EAGER=True` in `.env`, async tasks run inline, so Terminal 4 is optional.
- Frontend runs at `<http://localhost:5173>` and proxies API calls to backend at `<http://localhost:8000>`.

### Docker (Optional)

```bash
docker compose up --build
```

- Frontend: <http://localhost:3000>

## 📡 API Endpoints

- POST `/api/accounts/login/` - Login
- GET `/api/dashboard/` - Dashboard summary
- GET `/api/employees/` - List employees
- GET `/api/employees/{id}/` - Employee profile
- POST `/api/employees/` - Create employee
- POST `/api/meetings/upload/` - Upload transcript
- POST `/api/meetings/upload/` - Upload meeting file/transcript for async intelligence pipeline
- POST `/api/meetings/map-speakers/` - Map diarized speakers to employee IDs
- GET `/api/meetings/{id}/insights/` - Meeting-level intelligence output
- POST `/api/meetings/upload-recording/` - Upload audio/video for ASR + analysis
- GET `/api/meetings/analysis/{meeting_id}/` - Meeting analysis detail
- GET `/api/meetings/analysis/employee/{employee_id}/` - Employee trend insights (legacy route)
- GET `/api/employees/{id}/meeting-insights/` - Employee-level meeting intelligence metrics
- GET `/api/meetings/` - List meetings
- GET `/api/employee-insights/{id}/` - AI insights
- GET `/api/attrition/{id}/` - Attrition risk
- POST `/api/ai/query/` - RAG AI query

## 🤖 AI Features

- **Transcript Summarization** — OpenAI or extractive fallback
- **Sentiment Analysis** — TextBlob (local, no API key)
- **Embedding Generation** — OpenAI ada-002 or deterministic fallback
- **RAG Pipeline** — Query → Embed → Vector Search → LLM Answer
- **Topic Extraction** — Keyword-based NLP
- **Attrition Prediction** — Rule-based risk scoring

## 🧠 Meeting Intelligence Pipeline

```text
Upload Meeting (file + participants)
    -> Celery Task Queue
    -> Whisper ASR with timestamps
    -> Speaker diarization labels (Speaker_1..N)
    -> Transcript segment storage
    -> Existing transformer sentiment + summarization services
    -> Employee-level participation/engagement metrics
    -> Dashboard aggregates
```

The pipeline reuses existing transformer-based sentiment and summarization services without modifying their internal logic.

## 🔑 Environment Variables

Add `OPENAI_API_KEY` to `.env` for full AI capabilities. System works without it using built-in fallbacks.

## 📁 Project Structure

```text
TeamSense/
├── backend/
│   ├── teamsense/        # Django project settings
│   ├── core/             # URL routing, seed data
│   ├── employees/        # Employee CRUD
│   ├── meetings/         # Meeting upload & Celery tasks
│   ├── analytics/        # Dashboard, insights, attrition
│   └── ai_engine/        # Summarizer, sentiment, RAG, embeddings
├── frontend/
│   └── src/
│       ├── pages/        # Dashboard, Employees, Profile, AI Assistant
│       ├── components/   # Sidebar
│       └── services/     # API client
├── docker/               # Dockerfiles
└── docker-compose.yml
```
