## Project Structure

```
travel-agency-platform/
├── travel-agency-api/       # Booking & auth backend (FastAPI, port 8000)
├── Search-API/              # Flight/hotel/activity search backend (FastAPI, port 8002)
└── travel-agency-app/       # Frontend SPA (Vue 3 + Vite, port 5173)
```

## Running the Application

All three services must be running at the same time. Open three separate terminals.

### Terminal 1 — Booking API (port 8000)

```bash
cd travel-agency-api
uv run uvicorn app.main:app --reload --port 8000
```

On first run, SQLAlchemy automatically creates all database tables.

Seed a test user by visiting:
```
http://localhost:8000/api/v1/setup-seed-data/
```

This creates a test account:
- **Email:** `test@example.com`
- **Password:** `CMPE-131@2026`

### Terminal 2 — Search API (port 8002)

```bash
cd Search-API/travel-agency-platform-service
uv run uvicorn app.main:app --reload --port 8002
```

### Terminal 3 — Frontend (port 5173)

```bash
cd travel-agency-app
npm install
npm run dev
```

---

## Accessing the App

The app is multi-tenant. Each agent is accessed via a different hostname.

Add these entries to your system hosts file:

**Windows** — edit `C:\Windows\System32\drivers\etc\hosts` as Administrator:
```
127.0.0.1  agenta.local
127.0.0.1  agentb.local
```

**Mac/Linux** — edit `/etc/hosts`:
```
127.0.0.1  agenta.local
127.0.0.1  agentb.local
```

Then open in your browser:

| URL | Tenant |
|-----|--------|
| http://agenta.local:5173 | Agent 1 |
| http://agentb.local:5173 | Agent 2 |

---

## Features

- **Search** flights, hotels, and activities by destination and date
- **Price Trends** — view historical flight price data with interactive chart
- **Book** flights, hotels, and activities in one booking
- **My Trips** — view saved bookings per agent and user
- **Edit** flight and hotel reservation dates/times
- **Login** with email and password

---

## API Documentation

Once the servers are running, interactive API docs are available at:

- Booking API: http://localhost:8000/docs
- Search API: http://localhost:8002/docs
