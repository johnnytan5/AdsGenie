# AdsGenie Backend

FastAPI backend application for AdsGenie.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API routes
│   │   └── v1/
│   │       ├── api.py          # Main API router
│   │       └── endpoints/      # Individual endpoint modules
│   └── core/                   # Core configuration
│       └── config.py          # Application settings
├── requirements.txt
├── .env.example
└── README.md
```

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

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/health` - API health check

## Development

- Add endpoints in `app/api/v1/endpoints/`
- Register new routers in `app/api/v1/api.py`
