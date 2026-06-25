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

---

## Deployment (Render)

The application is deployed on [Render](https://render.com) as two separate
services provisioned by the `render.yaml` blueprint at the project root.

### Live URLs

| Service  | URL |
|----------|-----|
| Backend  | `https://crypto-bank-api.onrender.com` |
| Frontend | `https://crypto-bank-frontend.onrender.com` |

> **Note:** Free-tier Render services spin down after 15 minutes of inactivity.
> The first request after a cold start may take 30–60 seconds.

### Deployment architecture

```
GitHub (main branch)
       │
       │  git push  (auto-deploy trigger)
       ▼
 ┌─────────────────────────────────────────────┐
 │                  Render                      │
 │                                             │
 │  ┌──────────────────┐  ┌─────────────────┐  │
 │  │  Web Service     │  │  Static Site    │  │
 │  │  (Python/Flask)  │  │  (React/CRA)    │  │
 │  │                  │  │                 │  │
 │  │  build:          │  │  build:         │  │
 │  │  pip install…    │  │  npm install    │  │
 │  │                  │  │  npm run build  │  │
 │  │  start:          │  │                 │  │
 │  │  gunicorn run:app│  │  serve: ./build │  │
 │  │                  │  │                 │  │
 │  │  PORT injected   │  │  SPA rewrites   │  │
 │  │  by Render       │  │  /* → index.html│  │
 │  └──────────────────┘  └─────────────────┘  │
 └─────────────────────────────────────────────┘
```

### How Render auto-deploy works

1. **Blueprint import** — the `render.yaml` file at the repository root defines
   both services.  When you connect the repository on the Render dashboard,
   Render reads this file and creates the services automatically.
2. **GitHub webhook** — Render registers a webhook on the connected repository.
   Every push to `main` fires the webhook and triggers a new deploy for each
   service listed in `render.yaml` (`autoDeploy: true`).
3. **Isolated build environments** — each service gets a fresh, isolated
   container.  The backend runs `pip install -r requirements.txt` then starts
   Gunicorn; the frontend runs `npm install && npm run build` and serves the
   resulting `build/` directory as a CDN-backed static site.
4. **Environment variables** — secrets (e.g. `SECRET_KEY`) and cross-service
   URLs (e.g. `REACT_APP_API_URL`, `FRONTEND_URL`) are configured once in the
   Render dashboard.  They are injected at build and runtime and never stored
   in source control.
5. **Zero-downtime deploys** — Render keeps the old instance running until the
   new build passes its health check, then switches traffic atomically.

### First-time setup

```bash
# 1. Push the repository to GitHub (the main branch).
# 2. Visit https://dashboard.render.com → New → Blueprint.
# 3. Select your forked/cloned repository.
# 4. Render reads render.yaml and creates both services.
# 5. After the first successful deploy, copy each service's public URL and
#    set the cross-service env vars in the Render dashboard:
#      - crypto-bank-api   →  FRONTEND_URL = <frontend URL>
#      - crypto-bank-frontend → REACT_APP_API_URL = <backend URL>
# 6. Trigger a manual re-deploy of both services so the new values take effect.
```

### CI/CD compatibility

The Render deployment does **not** conflict with the GitHub Actions CI pipeline:

* CI (`.github/workflows/ci.yml`) runs lint, security scans and tests on every
  push to **any** branch.  It does not deploy.
* Render's auto-deploy only fires on pushes to `main` (controlled by
  `autoDeploy: true` in `render.yaml`).
* Backend tests always use `sqlite:///:memory:` (see `config.py`
  `TestingConfig`), so they pass in CI even when `DATABASE_URL` is absent.
* The frontend build in CI runs without `REACT_APP_API_URL` set; `axios` falls
  back to relative paths, which is fine because no live requests are made.
