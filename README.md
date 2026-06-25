# Crypto-Bank-App

Level 6 Software Engineering & Agile Project

A full-stack web application for managing cryptocurrency wallets with a Flask backend and React frontend.

## Project Structure

```
/backend          Flask REST API
  /app            Application package (models, routes, validators, errors)
  /tests          pytest test suite
  config.py       Environment-aware configuration
  requirements.txt Python dependencies
  run.py          Development server entry point

/frontend         React (Create React App) frontend
  /src            Source components, pages, utils
  package.json    Node dependencies and scripts

/docker           Container build files
  Dockerfile.backend
  Dockerfile.frontend
  docker-compose.yml

/.github/workflows
  ci.yml          GitHub Actions CI pipeline

.env.example      Template for environment variables
```

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 20+

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
# API available at http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm start
# App available at http://localhost:3000
```

---

## Running Tests

### Backend tests (pytest)

```bash
cd backend
pytest -q
```

All tests use an in-memory SQLite database and require no environment variables.

### Frontend tests (Jest + React Testing Library)

```bash
cd frontend
npm test
```

---

## Linting & Security

### Backend

```bash
cd backend
# Lint
flake8 app/ --max-line-length=120

# Security scan
bandit -r app/ -ll

# Dependency vulnerability audit
pip-audit
```

### Frontend

```bash
cd frontend
npm run lint
```

---

## Building Docker Images

Both images are built from the repository root so they can copy code from
the correct paths.

```bash
# Backend image
docker build -f docker/Dockerfile.backend -t crypto-bank-backend .

# Frontend image
docker build -f docker/Dockerfile.frontend -t crypto-bank-frontend .

# Or use Compose to build and run both together
docker-compose -f docker/docker-compose.yml up --build
```

---

## CI/CD

GitHub Actions runs automatically on every push and pull request to `main`:

1. **Backend job** — installs Python deps, runs flake8, bandit, then pytest
2. **Frontend job** — installs Node deps, runs ESLint, then `npm run build`

See `.github/workflows/ci.yml` for the full pipeline definition.

---

## Windows Deployment (Legacy)

The original PowerShell/batch launcher scripts are preserved in `deployment/`
for running the app directly on Windows without Docker:

```powershell
cd deployment
.\start.bat   # start backend + frontend
.\stop.bat    # stop both processes
```
