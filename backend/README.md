# Private Class App Backend

Django REST backend for the coaching MVP.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API

- Admin: `http://localhost:8000/admin/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`
- JWT login: `POST /api/auth/token/`
- JWT refresh: `POST /api/auth/token/refresh/`

## MVP Domain Loop

1. A coach creates an availability slot.
2. A student creates a booking request for that slot.
3. The coach accepts or rejects the request.
4. On acceptance, a session is created and the slot is reserved.
5. Coach or student can cancel according to the coach policy.
