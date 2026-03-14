# TeamSense — AI HR Intelligence Platform

An AI-powered organizational memory system for HR teams. Ingest employee meeting transcripts, analyze sentiment, extract insights, and query employee history using RAG.

## 🏗️ Architecture

```
User → React Dashboard → Django REST API → AI Processing Layer → PostgreSQL + PGVector
                                         → Celery Workers (Redis)
```

## 🚀 Quick Start

### Docker (Recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000

### Local Development

**Backend:**
```bash
cd backend
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker (optional):**
```bash
cd backend
celery -A teamsense worker -l info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/` | Dashboard summary |
| GET | `/api/employees/` | List employees |
| GET | `/api/employees/{id}/` | Employee profile |
| POST | `/api/employees/` | Create employee |
| POST | `/api/meetings/upload/` | Upload transcript |
| GET | `/api/meetings/` | List meetings |
| GET | `/api/employee-insights/{id}/` | AI insights |
| GET | `/api/attrition/{id}/` | Attrition risk |
| POST | `/api/ai/query/` | RAG AI query |

## 🤖 AI Features

- **Transcript Summarization** — OpenAI or extractive fallback
- **Sentiment Analysis** — TextBlob (local, no API key)
- **Embedding Generation** — OpenAI ada-002 or deterministic fallback
- **RAG Pipeline** — Query → Embed → Vector Search → LLM Answer
- **Topic Extraction** — Keyword-based NLP
- **Attrition Prediction** — Rule-based risk scoring

## 🔑 Environment Variables

Add `OPENAI_API_KEY` to `.env` for full AI capabilities. System works without it using built-in fallbacks.

## 📁 Project Structure

```
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
