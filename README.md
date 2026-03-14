# TeamSense

AI-powered HR intelligence platform for employee analytics, meeting insights, attrition risk support, and unified multi-source data ingestion.

## What This Project Delivers

- Unified HR dashboard for employees, meetings, and AI insights
- Role-aware access for HR and CHR workflows
- AI assistant for HR analytics Q and A
- Meeting intelligence with transcript, summary, and sentiment
- Attrition support components
- Data Aggregation Engine that ingests from multiple sources into one normalized pipeline

## Data Aggregation Engine

The ingestion system is designed so HR teams do not manually consolidate employee data.

### Stage 1: Data Connectors

- HRMS integration path (Zoho command and connector scaffolding)
- CSV and Excel upload connector
- Slack connector
- Google Forms connector
- Internal document connector for meeting notes

### Stage 2: Data Normalization

All source inputs are normalized to a unified internal format.

Employee Data

- employee_id
- name
- department
- manager
- join_date

Feedback Data

- employee
- source
- sentiment
- timestamp

Meeting Data

- participants
- summary
- sentiment

### Stage 3: Storage

Normalized records are persisted into:

- Employee
- Feedback
- Meeting
- Sentiment Insights

### Stage 4: AI Processing

Each normalized payload is routed through AI processing for:

- sentiment analysis
- summarization
- insight generation

### Stage 5: Dashboard Sync

Processed records automatically update employee profile views and ingestion status dashboards.

## Tech Stack

Backend

- Django + Django REST Framework
- Celery + Redis
- SQLite for local development
- PostgreSQL service in Docker environment

Frontend

- React + Vite
- Axios
- React Router

AI and Data

- TextBlob sentiment
- Transformer ecosystem dependencies
- Pandas and OpenPyXL for tabular ingestion

## Project Structure

- backend: Django APIs, AI services, ingestion workers
- frontend: React application and pages
- docker: Dockerfiles and entrypoint scripts
- docker-compose.yml: full stack services

## Environment Variables

Create a root .env file and fill only values you need.

Core

- DEBUG=True
- DJANGO_SECRET_KEY=replace_with_secure_key
- ALLOWED_HOSTS=*
- CELERY_BROKER_URL=redis://localhost:6379/0

Optional Connectors

- SLACK_BOT_TOKEN=your_slack_bot_token
- GOOGLE_SERVICE_ACCOUNT=path_to_google_service_account_json
- OPENAI_API_KEY=optional_for_openai_features

Zoho Connector

- ZOHO_CLIENT_ID=your_client_id
- ZOHO_CLIENT_SECRET=your_client_secret
- ZOHO_REDIRECT_URI=<http://localhost:8000/api/ingestion/zoho-callback/>

Security note

- Never commit real secrets to git.

## Local Development Setup

Backend terminal

1. cd backend
2. pip install -r requirements.txt
3. python manage.py migrate
4. python manage.py seed_data
5. python manage.py runserver

Celery worker terminal

1. cd backend
2. celery -A teamsense worker -l info

Frontend terminal

1. cd frontend
2. npm install
3. npm run dev

App URLs

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000/api>

## Docker Setup

Run everything with Docker:

1. docker compose up --build

Default service ports

- Frontend: 3000
- Backend: 8000
- PostgreSQL: 5432
- Redis: 6379

## Ingestion APIs

Main endpoints under /api/ingestion:

- POST /upload-csv/
- POST /slack/
- POST /google-forms/
- POST /upload-document/
- GET /overview/
- GET /jobs/
- GET /feedback/

Behavior

- Requests create async ingestion jobs
- Jobs are processed by Celery workers
- Status can be tracked from jobs and overview endpoints

## Typical Ingestion Flow

1. Queue data from one connector
2. Pipeline normalizes records into internal schema
3. Data is persisted to Employee, Feedback, Meeting, and Sentiment Insights
4. AI enriches records with sentiment, summaries, and insights
5. Dashboard updates with latest job and profile data

## Quality Checks

Backend

- python manage.py check

Frontend

- npm run build

## Troubleshooting

Backend does not start

- Ensure migrations are applied
- Ensure dependencies are installed
- Verify .env variables for optional connectors

Celery worker fails

- Confirm Redis is running
- Check CELERY_BROKER_URL value

Frontend white screen

- Run npm run build to catch compile issues
- Open browser console and resolve runtime import errors

Ingestion jobs remain queued

- Ensure Celery worker is running
- Check backend logs for job failures

## Recommended Demo Sequence

1. Login as HR or CHR user
2. Open Ingestion page
3. Queue one CSV ingestion and one document ingestion
4. Open Jobs section and verify status transitions
5. Open employee and meeting pages to show auto-updated insights

## License

Use according to your team or hackathon guidelines.
