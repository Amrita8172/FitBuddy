# FitBuddy — AI Fitness Plan Generator

Complete FastAPI + SQLite + SQLAlchemy + Jinja2 project based on the supplied FitBuddy specification.

## Included
- Cleaner responsive frontend using HTML/CSS/vanilla JS; no Bootstrap
- 7-day personalized workout generation
- AI nutrition/recovery tip
- Feedback-based plan revision
- SQLite persistence with SQLAlchemy
- Admin dashboard with HTTP Basic authentication
- JSON API + Swagger docs
- Gemini integration through the current `google-genai` SDK
- Local demo fallback when no Gemini key is configured
- Health endpoint and tests

## Run on Windows
```powershell
cd FitBuddy_AI_Fitness_Plan_Generator
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

API docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health
Admin: http://127.0.0.1:8000/admin

Set `GOOGLE_API_KEY` in `.env` for live Gemini responses. Without a key, the app automatically uses a deterministic local demo generator, so setup and tests still work.

Default admin credentials are `admin` / `change-this-admin-password`; change them in `.env`.

## Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

## API
`POST /api/generate-workout`
```json
{"username":"Alex","user_id":"FB1001","age":22,"weight":65,"goal":"muscle gain","intensity":"medium"}
```

`POST /api/submit-feedback`
```json
{"user_id":"FB1001","feedback":"Add more cardio and one extra rest day."}
```

`GET /api/users/FB1001`

`DELETE /api/users/FB1001` requires admin Basic Auth.

## Tests
```powershell
python -m pytest -q
```

## Gemini note
The source document mentions older Gemini 1.5 Pro/Flash and the legacy `google-generativeai` package. This implementation uses the current `google-genai` SDK and configurable model names in `.env`. If a selected model is unavailable for your API account, change the model names to a currently available Gemini model. The app catches API failures and falls back to local demo output.

## Database
SQLite is automatic. `fitbuddy.db` is created when the server starts. No MySQL/PostgreSQL setup is required.

## Production
Use HTTPS, proper authentication, secret management, rate limiting, structured logging, a managed DB, and a production ASGI deployment. FitBuddy is general wellness software, not medical advice.
