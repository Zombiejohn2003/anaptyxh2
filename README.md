# Sensor Monitoring Dashboard

React + Flask web application for monitoring and managing sensor data with role-based access control.

## Features

- JWT authentication; unauthenticated users only see the login screen.
- Two roles:
  - `user`: read-only access to dashboard, sensors, and charts.
  - `admin`: full CRUD for sensors and users.
- Dashboard with four summary cards, two aggregate charts, sensor table, and admin-only users table.
- Sensor detail page with metadata and configurable time-series aggregation by hour, day, or month.
- PostgreSQL schema with users, sensors, measurement categories, sensor-category relations, and historical measurements.
- Bonus ingestion endpoint: `POST /api/measurements/ingest` protected by `X-API-Key`.

## Tech stack

- Backend: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, PostgreSQL.
- Frontend: React, Vite, Axios, Recharts, Lucide icons.
- Database: PostgreSQL 16 through Docker Compose.

## Quick start

1. Start PostgreSQL:

   ```bash
   docker compose up -d db
   ```

2. Configure environment:

   ```bash
   cp .env.example .env
   export DATABASE_URL=postgresql+psycopg2://sensor_user:sensor_password@localhost:5432/sensor_dashboard
   export JWT_SECRET_KEY=dev-secret
   export INGEST_API_KEY=dev-ingest-token
   export FRONTEND_ORIGIN=http://localhost:5173
   ```

3. Install and seed the Flask backend:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python seed.py
   python run.py
   ```

4. Install and run the React frontend in a second terminal:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Open `http://localhost:5173`.

Demo accounts:

- Admin: `admin` / `admin123`
- Simple user: `user` / `user123`

## SQL dump

`database/schema_seed.sql` contains the PostgreSQL schema and seed data. To load it manually:

```bash
psql postgresql://sensor_user:sensor_password@localhost:5432/sensor_dashboard -f database/schema_seed.sql
```

## API highlights

- `POST /api/auth/login`
- `GET /api/dashboard`
- `GET /api/sensors`
- `GET /api/sensors/<id>`
- `GET /api/sensors/<id>/measurements?resolution=hour|day|month`
- Admin only: `POST|PUT|DELETE /api/sensors`
- Admin only: `GET|POST|PUT|DELETE /api/users`
- External ingestion: `POST /api/measurements/ingest` with header `X-API-Key: dev-ingest-token`
