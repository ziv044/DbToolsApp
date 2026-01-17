# DbToolsApp

Multi-tenant SQL Server management platform.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16
- SQL Server ODBC Driver 18

## Quick Setup

Run the setup script from PowerShell:

```powershell
.\scripts\setup.ps1
```

## Manual Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run development server
python run.py
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | dev-secret-key |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://postgres:1234@localhost:5432/dbtools_system |
| `PORT` | Backend server port | 5000 |

## Project Structure

```
DbToolsApp/
├── backend/           # Flask API
│   ├── app/          # Application package
│   ├── tests/        # Backend tests
│   └── run.py        # Entry point
├── frontend/         # React SPA
│   ├── src/          # Source code
│   └── dist/         # Build output
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## Development

### Backend

```bash
cd backend
venv\Scripts\activate

# Run tests
pytest

# Run with auto-reload
python run.py
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Lint
npm run lint

# Format
npm run format

# Build
npm run build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
