# SAF Hack Backend

Backend MVP built with FastAPI and SQLite.

## Start locally

From the `backend/` folder:

```bash
python -m venv .venv
```

Activate the virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## MVP endpoints currently available

- `GET /health`
- `GET /api/v1/users/me`
- `GET /api/v1/spaces`
- `GET /api/v1/services`
- `GET /api/v1/availability?space_id=fitness&date=2026-11-10`
- `POST /api/v1/reservations`
- `GET /api/v1/reservations?user_id=demo-user`

The SQLite database is created locally on first startup and is intentionally ignored by Git.

All seeded data is synthetic demo data. No SAF challenge dataset is committed.
