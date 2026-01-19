# Artist Playlist Placement Tracker - Backend

FastAPI backend service for tracking Spotify artist playlist placements.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file (copy from `env.example`):
```bash
cp env.example .env
# Edit .env with your settings
```

4. Run the server:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Access API docs:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── core/
│   │   └── config.py    # Configuration and settings
│   ├── api/             # API routes (to be added)
│   ├── models/          # Database models (to be added)
│   ├── schemas/         # Pydantic schemas (to be added)
│   └── services/        # Business logic (to be added)
├── requirements.txt
└── README.md
```
