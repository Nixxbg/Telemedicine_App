# Telemedicine Backend

FastAPI backend for the telemedicine application.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file (see `.env` for example)

3. Run the application:

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:

- API docs: http://localhost:8000/api/v1/docs
- Alternative docs: http://localhost:8000/api/v1/redoc

## Health Check

- Health endpoint: http://localhost:8000/health

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
└── src/
    ├── api/
    │   └── v1/
    │       ├── api.py      # Main API router
    │       └── endpoints/  # API endpoint modules
    ├── core/
    │   ├── config.py       # Application configuration
    │   └── database.py     # Database configuration
    ├── models/             # SQLAlchemy models
    ├── schemas/            # Pydantic schemas
    └── services/           # Business logic services
```
