# Implementation report

## Environment

- Python 3 with Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, psycopg2.
- Node.js with React, Vite, Axios, Recharts, and Lucide React.
- PostgreSQL 16, started with Docker Compose.

## Installation

1. Start PostgreSQL with `docker compose up -d db`.
2. Copy `.env.example` to `.env` or export the same variables in the shell.
3. In `backend/`, create a virtual environment, install `requirements.txt`, run `python seed.py`, and start `python run.py`.
4. In `frontend/`, run `npm install` and `npm run dev`.

## Architecture

The backend exposes a REST API under `/api`. Authentication uses JWT tokens. The `admin_required`
decorator protects all write operations for sensors and users, while regular authenticated users can
read dashboard and sensor information.

The database contains normalized tables for users, sensors, measurement categories, the many-to-many
relationship between sensors and categories, and historical measurements. Temperature and humidity are
stored as category rows and are loaded dynamically by the frontend sensor form.

The frontend keeps the access token in `localStorage`, redirects unauthenticated visitors to the login
screen, and conditionally renders admin-only tables and forms. Dashboard charts use aggregate API data,
while the sensor detail chart requests server-side aggregation by hour, day, or month.

## Bonus endpoint

`POST /api/measurements/ingest` accepts external readings when the caller supplies the configured
`X-API-Key`. The endpoint validates that the sensor exists and that the submitted measurement category
is enabled for that sensor before storing the reading.
