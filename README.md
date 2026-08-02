# Yash Technology Outreach Hub

A manual-first B2B lead-generation and outreach tool for Yash Technology.

This repo now has two parts:
- `backend/`: Python FastAPI backend with SQLAlchemy, PostgreSQL, Alembic, and pandas
- `frontend/`: Streamlit UI that talks only to the FastAPI backend over HTTP

## Current Status

Phase 1 is the active phase.

Phase 1 includes:
- Companies, Contacts, Campaigns, Mailboxes, Messages, Replies, and Audit Events
- CSV import for companies and contacts
- Manual draft creation
- Manual send marking
- Reply logging
- Follow-up scheduling
- Dashboard metrics for total contacts, messages sent this month, reply rate, and product-line breakdown
- Hard per-mailbox send throttling
- STOP opt-out enforcement
- Hard delete for contacts

Phase 2A discovery is now implemented:
- Apollo-only automated discovery
- ICP-driven organization and people search
- Provider manager layer with Apollo as the only enabled provider
- Raw discovery staging before CRM import
- Rule-based qualification and scoring
- Duplicate merge using existing CRM rules
- Discovery run tracking and metrics

The current semi-automated workflow is now UI-first:
- on-demand discovery jobs from Streamlit
- background execution after a user click
- lead review, draft editing, and bulk send from the UI
- daily lead targets by product segment
- workspace settings for batch size and SMTP defaults

Phase 2B, Phase 3, and Phase 4 remain planned.

## Why This Stack

- Backend: Python 3.11+ with FastAPI, because you requested Python only for all server-side logic, APIs, and jobs
- Database: PostgreSQL with SQLAlchemy and Alembic, because this is a proper shared CRM-style system and will grow beyond a single-file database
- CSV handling: pandas, because imports and exports are a core workflow for this app
- Frontend: Streamlit, because it is fast to ship and stays fully separate from the backend
- Scheduler: APScheduler, because Phase 4 is a single-server follow-up check use case and does not need the overhead of Celery yet

## How Data Enters The System

The system is intentionally manual-first.

Primary sources:
- Sales Navigator CSV exports
- Apollo CSV exports
- Human-created company and contact records in the UI
- Later, verified enrichment APIs such as Apollo or Hunter for email validation

Not allowed:
- LinkedIn scraping
- Arbitrary web scraping for email harvesting
- Auto-send in Phase 1

Important behavior:
- STOP is not auto-detected from inbound replies in Phase 1; a human must read the reply and mark the contact do not contact if needed
- Duplicate contact imports are skipped when the same contact already exists
- Duplicate company imports reuse the existing company and merge any new product-fit values
- Missing companies in a contacts CSV are auto-created during import

What you import today:
- Companies from CSV or the UI
- Contacts from CSV or the UI

What you do not import automatically:
- LinkedIn profile data by scraping
- Personal/home data
- Unverified bulk contact data

## Business Rules That Are Built In

- Every outbound email must include `Reply STOP to stop hearing from us.`
- If a contact is bounced or requested removal, the record is flagged as do not contact
- Contact records are limited to business-context fields only
- Hard delete is supported on contact records
- Sending is capped per mailbox in code

## Repository Layout

- `backend/app/main.py`: FastAPI app entrypoint
- `backend/app/api/routes.py`: REST endpoints for Phase 1
- `backend/app/api/discovery_routes.py`: Phase 2A discovery endpoints
- `backend/app/models/base.py`: SQLAlchemy ORM models
- `backend/app/schemas.py`: Pydantic request and response models
- `backend/app/discovery/`: Apollo provider, ICP loader, qualification, and discovery engine
- `backend/app/services/outreach.py`: business logic for opt-out, throttling, audits, dashboard helpers
- `backend/app/services/discovery_merge.py`: shared CRM merge helpers for discovery and imports
- `backend/app/services/csv_service.py`: CSV parsing helpers
- `backend/app/jobs/scheduler.py`: APScheduler discovery job registration
- `backend/alembic/`: migration setup
- `frontend/streamlit_app.py`: Streamlit frontend
- `backend/.env`: local environment values
- `backend/.env.example`: template for the environment file

## Data Model

The backend stores these core entities:
- Company
- Contact
- Campaign
- Mailbox
- Message
- Reply
- Audit Event
- Company Product Fit join table

### Company

Fields:
- Name
- Industry
- Source
- Notes
- Product fit

Product fit values:
- Industrial Vacuum Cleaning Systems
- Warehouse & Storage Solutions
- GFRP Rebar and customised bend elements

### Contact

Fields:
- Name
- Title
- Company
- Work email
- Work phone
- LinkedIn URL
- Do not contact
- Added date
- Source

### Message

Fields:
- Contact
- Campaign
- Mailbox
- Subject
- Body
- Status
- Sent date
- Sequence step
- Follow-up date

Message statuses:
- Draft
- Sent
- Replied
- Bounced

### Reply

Fields:
- Message
- Contact
- Body
- Received date
- Outcome

### Audit Event

Each important action is logged with:
- Entity type
- Entity id
- Action
- Reason
- Metadata
- Timestamp

This supports the DPDP-style audit trail requirement you gave earlier.

## Where Credentials Live

All credentials and environment-specific values belong in `backend/.env`.

Examples:
- PostgreSQL connection string
- Apollo API key
- Hunter API key
- OpenAI API key
- Anthropic API key
- SMTP host
- SMTP user
- SMTP password
- SMTP from address
- Redis URLs

Do not hardcode those into source files.

## Environment Variables

See [backend/.env.example](backend/.env.example) for the full template.

Important values:
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: allowed frontend origins
- `FRONTEND_BASE_URL`: frontend base URL
- `DEFAULT_DAILY_SEND_LIMIT`: mailbox send cap
- `WRITE_API_KEY`: shared key required for write endpoints
- `APOLLO_BASE_URL`: Apollo API base URL
- `APOLLO_API_KEY`: Phase 2 enrichment
- `APOLLO_DAILY_CALL_LIMIT`: daily Apollo call cap
- `APOLLO_MAX_COMPANIES_PER_RUN`: per-run company cap
- `APOLLO_MAX_CONTACTS_PER_COMPANY`: per-company contact cap
- `APOLLO_MIN_SECONDS_BETWEEN_CALLS`: cooldown between Apollo requests
- `APOLLO_RETRY_LIMIT`: retry count for Apollo requests
- `DISCOVERY_ENABLED_PROVIDERS`: comma-separated enabled provider list, default `apollo`
- `DISCOVERY_SCHEDULE_HOUR_UTC`: discovery scheduler hour
- `DISCOVERY_SCHEDULE_MINUTE_UTC`: discovery scheduler minute
- `HUNTER_API_KEY`: Phase 2 enrichment alternative
- `OPENAI_API_KEY`: Phase 3 drafting
- `ANTHROPIC_API_KEY`: Phase 3 drafting alternative
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`: sending credentials for future phases
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`: future background job support

## Local Setup

### 1. Copy the environment file

Create `backend/.env` from `backend/.env.example`.

### 2. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Create the database

Create a PostgreSQL database named something like `yash_outreach`, then update `DATABASE_URL` in `backend/.env`.

Example:

```env
DATABASE_URL="postgresql+psycopg://postgres:root@localhost:5432/yash_outreach"
```

Also set `WRITE_API_KEY` in `backend/.env`. The Streamlit frontend reads the same file and sends that key as `X-API-Key` on POST and DELETE requests.
Also set `APOLLO_API_KEY` and the discovery limits in `backend/.env` before using Phase 2A.

Default discovery values shipped in the backend config:
- `APOLLO_DAILY_CALL_LIMIT=500`
- `APOLLO_MAX_COMPANIES_PER_RUN=50`
- `APOLLO_MAX_CONTACTS_PER_COMPANY=10`

In practice, discovery will stop once it has spent 500 Apollo HTTP calls in a day, and a single run will only process up to 50 companies and 10 people per company. The actual Apollo request cost depends on pagination and retries, but these caps bound both daily API usage and lead volume.

### 4. Run migrations

```bash
cd backend
alembic upgrade head
```

This applies both the Phase 1 schema and the Phase 2 discovery migration.

### 5. Start the FastAPI backend

```bash
cd backend
uvicorn app.main:app --reload
```

Backend default:
- `http://localhost:8000`

### 6. Start the Streamlit frontend

```bash
streamlit run frontend/streamlit_app.py
```

Frontend default:
- `http://localhost:8501`

## Phase 2A Discovery

The discovery flow is Apollo-only and runs through the new scheduler-backed discovery engine.

Lead scoring is implemented in Phase 2A and is used during discovery qualification and CRM import. It is not a future Phase 2 item anymore.
Apollo remains the only enabled provider in the current Provider Manager setup; the manager exists so future licensed providers can be added without changing the qualification, dedupe, or CRM import layers.

Qualification is now fully explainable and persisted for review:
- every discovered company keeps a stored qualification result, including rule-by-rule PASS/FAIL breakdowns
- discovery staging now preserves qualified, manual review, rejected, and imported outcomes
- run summaries include evaluated count, imported/manual review/rejected counts, average score, and top failure reasons
- scoring values and thresholds are configurable in `backend/app/config/icp.yml`
- the Discovery Staging UI shows the stored qualification summary for each record

High-level pipeline:
- Scheduler
- Discovery engine
- ICP loader
- Apollo provider
- Discovery staging
- Qualification
- Lead scoring
- Duplicate detection and merge
- CRM import
- Audit events

Useful discovery endpoints:
- `GET /discovery/icp`
- `POST /discovery/run`
- `GET /discovery/runs`
- `GET /discovery/runs/{run_id}`
- `GET /discovery/staging`
- `GET /discovery/manual-review`
- `GET /discovery/summary`
- `POST /discovery/run` now accepts on-demand lead discovery inputs and queues a background job when those fields are provided
- `GET /discovery/jobs`
- `GET /discovery/jobs/{job_id}`
- `POST /discovery/jobs/{job_id}/cancel`
- `GET /dashboard/stats`
- `GET /drafts`
- `POST /drafts/generate`
- `PUT /drafts/{id}`
- `GET /daily-targets`
- `PUT /daily-targets`
- `GET /settings`
- `PUT /settings`
- `POST /messages/send-bulk`

The Streamlit app now includes pages for Dashboard, Lead Discovery, Lead Review, Email Drafts, Send Emails, Analytics, and Settings.
Run statuses are `running`, `completed`, and `failed`. Failed runs are shown in the discovery table and also called out with a visible warning in Streamlit.

## How To Use Phase 1

### Companies

You can:
- Add a company manually
- Import companies from CSV
- Assign one or more product-fit categories

CSV columns accepted:
- `company`
- `company name`
- `name`
- `industry`
- `source`
- `notes`
- `product fit`

### Contacts

You can:
- Add contacts manually
- Import contacts from CSV
- Link each contact to a company
- Mark a contact as do not contact
- Hard delete a contact

Contacts CSV behavior:
- If a row references a company name that does not exist, the backend creates that company automatically
- If the same contact already exists in the target company, the import skips that row
- The current dedupe rule uses work email when present, otherwise it falls back to the contact name plus title within the company

Manual contact creation does not yet auto-dedupe; it will rely on the database and your review process.

CSV columns accepted:
- `name`
- `title`
- `company`
- `source`
- `email`
- `phone`
- `linkedin url`

### Campaigns

Campaigns are optional organizing containers for outreach.

You can create a campaign and attach it to a primary company, or leave it unlinked.

### Mailboxes

Each mailbox has a hard daily send cap.

This is enforced in code, not just documented.

When a message is marked sent:
- the mailbox is checked
- the active daily sent count is checked
- the send is blocked if the mailbox is over limit

### Messages

The workflow is:
- Create a draft message
- Review it manually
- Mark it sent
- Log replies
- Schedule follow-ups

Phase 1 does not auto-send anything.

### Replies

Replies are manually logged.

When a reply is logged:
- the message status becomes replied
- the audit trail is updated
- future phases can use that reply history for follow-up logic

STOP handling:
- The backend does not auto-flag STOP from reply text in Phase 1
- If a human sees a STOP request, they should mark the contact do not contact or bounce the message depending on the situation

### Follow-ups

You can manually schedule a follow-up date on any message.

Phase 4 automation is not active yet.

## REST API Summary

Backend base URL:
- `http://localhost:8000`

Main endpoints:
- `GET /health`
- `GET /dashboard`
- `GET /companies`
- `POST /companies`
- `POST /companies/import`
- `GET /contacts`
- `GET /contacts/{contact_id}`
- `POST /contacts`
- `POST /contacts/import`
- `DELETE /contacts/{contact_id}`
- `GET /campaigns`
- `POST /campaigns`
- `GET /mailboxes`
- `POST /mailboxes`
- `GET /messages`
- `POST /messages/draft`
- `POST /messages/{message_id}/send`
- `POST /replies`
- `POST /messages/{message_id}/follow-up`
- `POST /messages/{message_id}/bounce`
- `GET /companies/export/csv`
- `GET /contacts/export/csv`

Write endpoints require the `X-API-Key` header to match `WRITE_API_KEY` from `backend/.env`.

## CSV Workflow

Use CSV imports when you already have lead lists from:
- Sales Navigator exports
- Apollo exports
- Manual list building

Recommended workflow:
- Import companies first
- Import contacts next
- Draft messages after contacts are linked to companies

## Phase 2 Plan

Planned later:
- Verified email enrichment through Apollo or Hunter
- Clear verification status in the UI

## Phase 3 Plan

Planned later:
- AI-assisted opening lines
- Draft-only output for human review
- Python SDK based provider integration

## Phase 4 Plan

Planned later:
- Scheduled follow-up checks
- Draft follow-ups only
- No auto-send unless explicitly approved later

## Security And Privacy Notes

- Keep all secrets in `backend/.env`
- Read endpoints are intentionally open in the current localhost-first setup; write endpoints require `X-API-Key`
- Do not store personal/home information
- Keep audit logging turned on
- Support hard deletion requests
- Do not scrape LinkedIn
- Do not bulk-harvest email addresses from arbitrary websites

## Troubleshooting

If the backend will not start:
- Check `DATABASE_URL`
- Confirm PostgreSQL is running
- Confirm migrations were applied
- Confirm your `.env` file is inside `backend/`

If the frontend cannot reach the backend:
- Confirm FastAPI is running on port `8000`
- Confirm Streamlit is using the correct `API_BASE_URL`
- Confirm CORS origins in `backend/.env`

If CSV import looks wrong:
- Check column names
- Make sure headers are present
- Make sure the file is UTF-8 or UTF-8 with BOM

## Legacy Note

The earlier Next.js prototype source has been removed from the repo.
The current implementation is Python backend + Streamlit frontend.
