# TeamSense - HR Data Ingestion Pipeline

## Placeholders to Replace ( .env )

```
ZOHO_CLIENT_ID=1000.IWODHOTGDFG94MSNMF0G75QX8YE77V
ZOHO_CLIENT_SECRET=3530ff12f3ca2142525ba2fc54faaa2cee0b3f2871
ZOHO_REDIRECT_URI=http://localhost:8000/api/ingestion/zoho-callback/

SLACK_BOT_TOKEN=xoxb-your-bot-token  # Slack App Bot Token
SLACK_CHANNEL=#hr-feedback

GOOGLE_SERVICE_ACCOUNT=path/to/service_account.json  # Download from Google Console
GOOGLE_FORM_ID=1your_google_form_id_here

BAMBOOHR_SUBDOMAIN=yourcompany  # mycompany.bamboohr.com
BAMBOOHR_API_KEY=your_api_key:x
```

## Run Local
```
cd backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py populate_dummy  # Test data
celery -A teamsense worker -l info  # Terminal 2
python manage.py runserver  # localhost:8000
```
Frontend: `cd frontend && npm run dev` → localhost:5173/ingestion

## Test Connectors
- **CSV**: localhost:5173/ingestion upload
- **Zoho**: localhost:8000/api/ingestion/zoho-auth/
- **Slack**: `python manage.py ingest_slack`
- **Forms**: `python manage.py ingest_forms`
- **Data**: localhost:8000/api/ingestion/feedback/

## BambooHR API Key
1. BambooHR → Profile → API Keys → Generate
2. Basic Auth: `{key}:x`

Ready. Replace placeholders → live data.
