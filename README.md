# Closira — AI-Powered Customer Enquiry Platform

Closira is a full-stack application that simulates an AI-powered customer enquiry handling workflow. The backend automatically processes inbound enquiries, matches them against Standard Operating Procedures (SOPs), handles escalations, and schedules follow-ups. The frontend provides a clean dashboard interface for managing and monitoring enquiries.

---

## Project Structure

```
closira/
├── backend/                     # FastAPI + SQLite backend service
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── enquiry_routes.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── constants.py
│   │   │   └── logging_config.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   ├── enquiry_schema.py
│   │   │   └── response_schema.py
│   │   ├── services/
│   │   │   ├── enquiry_service.py
│   │   │   ├── sop_matcher.py
│   │   │   ├── followup_service.py
│   │   │   └── escalation_service.py
│   │   ├── workers/
│   │   │   └── background_tasks.py
│   │   ├── utils/
│   │   │   ├── exceptions.py
│   │   │   └── helpers.py
│   │   └── logs/
│   ├── requirements.txt
│   ├── CLAUDE.md
│   └── README.md
│
└── frontend/                    # React frontend dashboard
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   └── App.jsx
    ├── package.json
    └── README.md
```

---

## Tech Stack

### Backend
| Layer         | Technology                        |
|---------------|-----------------------------------|
| Language      | Python 3.11+                      |
| Framework     | FastAPI                           |
| Database      | SQLite (via SQLAlchemy ORM)       |
| Validation    | Pydantic v2                       |
| Async Tasks   | FastAPI BackgroundTasks           |
| Config        | pydantic-settings                 |
| Logging       | Structured JSON (rotating files)  |

### Frontend
| Layer         | Technology                        |
|---------------|-----------------------------------|
| Framework     | React                             |
| HTTP Client   | Axios                             |
| Styling       | Tailwind CSS                      |
| Build Tool    | Vite                              |

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

---

## Backend Setup

### 1. Navigate to the backend directory

```bash
cd closira/backend
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.

The SQLite database file (`closira.db`) is created automatically in the `backend/` directory on first startup. No migrations needed.

---

## Frontend Setup

### 1. Navigate to the frontend directory

```bash
cd closira/frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm run dev
```

The frontend starts at `http://localhost:5173`.

> **Note:** The frontend is currently experiencing API connection issues with the backend. Certain features — including live enquiry status updates and the history timeline view — may not display correctly or may show empty states. This is a known issue and will be resolved in the next update. The backend APIs themselves are fully functional and can be tested independently via Swagger UI.

---

## API Documentation

Once the backend is running, interactive API docs are available at:

| Interface | URL                              |
|-----------|----------------------------------|
| Swagger   | http://localhost:8000/docs       |
| ReDoc     | http://localhost:8000/redoc      |
| Health    | http://localhost:8000/enquiry/health |

---

## API Endpoints

### POST `/enquiry/`
Create a new customer enquiry. Triggers background SOP matching immediately and returns the enquiry ID without waiting for processing to complete.

**Request:**
```json
{
  "channel": "chat",
  "customer_name": "Alice Johnson",
  "message": "Hi, I'd like to make a booking for next Friday."
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Enquiry received. Processing started in background.",
  "data": {
    "enquiry_id": 1,
    "status": "pending",
    "message": "Enquiry received. Processing started in background."
  }
}
```

---

### POST `/enquiry/{id}/follow-up`
Schedule a follow-up message for an enquiry.

**Request:**
```json
{
  "delay_minutes": 30,
  "message_template": "Just checking in — did we resolve your query?"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Follow-up scheduled in 30 minute(s).",
  "data": {
    "followup_id": 1,
    "enquiry_id": 1,
    "scheduled_time": "2024-06-01T15:00:00",
    "status": "scheduled"
  }
}
```

---

### POST `/enquiry/{id}/escalate`
Manually escalate an enquiry to a human agent.

**Request:**
```json
{
  "reason": "Customer is very upset and requesting a manager."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Enquiry has been escalated to a human agent.",
  "data": {
    "enquiry_id": 1,
    "status": "escalated",
    "message": "Enquiry has been escalated to a human agent."
  }
}
```

---

### GET `/enquiry/{id}/history`
Retrieve the full enquiry detail with conversation timeline, follow-ups, SOP match result, and escalation history.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Enquiry history retrieved successfully.",
  "data": {
    "id": 1,
    "customer_name": "Alice Johnson",
    "channel": "chat",
    "message": "Hi, I'd like to make a booking for next Friday.",
    "status": "resolved",
    "matched_sop": "Booking Enquiry",
    "suggested_response": "Thank you for reaching out! We'd be happy to help you with your booking...",
    "created_at": "2024-06-01T14:30:00",
    "updated_at": "2024-06-01T14:30:01",
    "timeline": [
      {
        "id": 1,
        "event_type": "enquiry_created",
        "message": "Enquiry received from Alice Johnson via chat.",
        "timestamp": "2024-06-01T14:30:00"
      },
      {
        "id": 2,
        "event_type": "task_started",
        "message": "Background processing started. Running SOP matching.",
        "timestamp": "2024-06-01T14:30:00"
      },
      {
        "id": 3,
        "event_type": "sop_matched",
        "message": "SOP matched: 'Booking Enquiry'. Suggested response generated and stored.",
        "timestamp": "2024-06-01T14:30:01"
      }
    ],
    "followups": []
  }
}
```

---

### GET `/enquiry/health`
Check API and database connectivity.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Service is healthy.",
  "data": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  }
}
```

---

## Enquiry Status Flow

```
POST /enquiry
      │
      ▼
  [pending]  ──── background task starts ────▶  [processing]
                                                      │
                              SOP matched? ───Yes───▶ [resolved]
                                          └──No────▶ [escalated]

POST /enquiry/{id}/escalate (manual override)
      │
      ▼
  [escalated]
```

---

## SOP Matching Engine

The backend uses a keyword-based SOP matching engine. Each inbound message is scanned for keywords across 5 categories. The category with the highest keyword hit count wins. If no keywords match, the enquiry is automatically escalated.

| SOP Category     | Trigger Keywords                                              |
|------------------|---------------------------------------------------------------|
| Booking Enquiry  | booking, reserve, appointment, schedule, book                 |
| Pricing Question | price, pricing, quote, cost, charge, fee, rate                |
| Complaint        | issue, complaint, unhappy, bad service, disappointed, terrible|
| After Hours      | closed, late, unavailable, after hours, weekend, holiday      |
| Support Request  | help, support, problem, assist, assistance, not working, error|

---

## Supported Channels

Enquiries can be submitted via the following channels:

- `email`
- `chat`
- `phone`
- `web`

---

## Logging

The backend emits structured JSON logs to two destinations simultaneously:

- **stdout** — visible in the terminal during development
- **`backend/app/logs/app.log`** — rotating file (5 MB per file, 3 backups kept)

Sample log line:
```json
{
  "timestamp": "2024-06-01T14:30:00.123Z",
  "level": "INFO",
  "logger": "app.workers.background_tasks",
  "message": "SOP matched.",
  "event_type": "sop_matched",
  "enquiry_id": 1,
  "sop": "Booking Enquiry"
}
```

Logged events: `enquiry_created`, `task_started`, `sop_matched`, `escalation_triggered`, `followup_created`, `followup_sent`, `manual_escalation`, `api_error`.

---

## Error Responses

All errors follow the same envelope:

```json
{
  "success": false,
  "message": "Enquiry with id=99 does not exist.",
  "detail": null
}
```

| Situation            | HTTP Code |
|----------------------|-----------|
| Enquiry not found    | 404       |
| Validation error     | 422       |
| Server error         | 500       |

---

## Configuration

Backend settings can be overridden via environment variables or a `.env` file placed in the `backend/` directory.

| Setting      | Default                 | Purpose                    |
|--------------|-------------------------|----------------------------|
| APP_NAME     | Closira Enquiry Backend | Shown in Swagger UI        |
| APP_VERSION  | 1.0.0                   | Shown in /health response  |
| DEBUG        | True                    | SQLAlchemy echo flag       |
| DATABASE_URL | sqlite:///./closira.db  | SQLite file path           |
| LOG_DIR      | app/logs                | Log directory              |
| LOG_FILE     | app/logs/app.log        | Rotating log file path     |

---

## Known Issues

| Area     | Issue                                                                 | Status       |
|----------|-----------------------------------------------------------------------|--------------|
| Frontend | API connection issues causing some views to not load correctly        | In progress  |
| Frontend | Live enquiry status updates and history timeline may show empty state | In progress  |

The backend REST APIs are fully functional. All endpoints can be tested independently via Swagger UI at `http://localhost:8000/docs`.

---

## What NOT to Commit

- `backend/closira.db` — auto-generated database file
- `backend/app/logs/` — runtime log files
- `.env` files — contain local secrets and config
- `__pycache__/` — Python bytecode cache
- `.venv/` or `venv/` — virtual environment directories
- `frontend/node_modules/` — npm packages

---

## License

This project is built as part of the Closira assignment. All rights reserved.
