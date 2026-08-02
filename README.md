# Driver Shift Engine

A shift-tracking app for an EV fleet. Drivers scan the car's QR code to tie themselves to a vehicle, photograph the dashboard, and Gemini reads the odometer and battery charge off the photo — no manual entry. Each shift's start/end mileage and charge are logged and turned into per-driver efficiency analytics.

---

## The problem it solves

An electric fleet needs to know, per shift: which driver drove which car, how far, and how much battery it cost. Done by hand, that's error-prone and constantly disputed. This app removes the manual step entirely — the driver just photographs the dashboard, and the numbers are read, validated, matched, and logged automatically.

## How a shift works

```
Driver logs in ──► scans car QR (ties driver to car) ──► photographs dashboard
                                                                │
                                                                ▼
                                        Gemini OCR reads odometer + battery %
                                                                │
                                          confidence >= 0.85 ? ──┼── no ──► ask driver to retake
                                                                │ yes
                                                                ▼
                                          logged as Shift Start (DB + Google Sheets)

   ... end of shift, same flow ...

   Shift End ──► matched to the open Shift Start ──► computes distance, battery used,
                 duration, and efficiency (km per % battery) ──► logged as a completed shift
```

## What makes it more than a CRUD app

**Making an unreliable model reliable.** Reading a value off a photographed dashboard is not a solved problem — glare, angle, and two completely different dashboard layouts (a tablet-style UI and a gauge-style UI) all break naive OCR. The Gemini integration uses layout-aware prompts tuned for each dashboard type and a confidence threshold: anything below 0.85 is rejected and the driver is asked to retake the photo, rather than logging a bad number. Bad input is refused at the source instead of corrected later.

**The database is the source of truth, not the spreadsheet.** Managers live in Google Sheets, so every shift is mirrored there — but Sheets is a reporting layer only. The Postgres/SQLAlchemy database is authoritative. When a Sheets write fails, a background worker retries it on a schedule instead of losing the row or blocking the driver.

**Failures are logged, not swallowed.** A dedicated exception table records duplicate shift starts, OCR failures, low-confidence reads, and Sheets sync failures — each with a type, message, related IDs, and an open/resolved status. Nothing fails silently.

## Architecture

Layered backend: `API routes → services → repositories → SQLAlchemy models`, with a separate integrations layer for Gemini, Google Cloud Storage, and Google Sheets.

Core tables: Driver, Car, DriverSession (JWT session tracking), ShiftStart, ShiftEnd, WholeShift (the matched, finalized pair with computed metrics), and ShiftException (the audit log).

Two background workers run on a schedule: one retries OCR for shifts stuck behind Gemini rate limits, one retries failed Sheets appends.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, JWT auth (python-jose)
- **Frontend:** Next.js (App Router), React, TypeScript, Arabic RTL UI
- **AI:** Google Gemini (dashboard OCR)
- **Storage:** Google Cloud Storage (dashboard photos), Google Sheets (reporting), PostgreSQL (source of truth)

## Running locally

The repo ships with no API keys, so the Gemini OCR step is inert until you supply your own — the rest of the app (auth, QR flow, shift matching, the full UI) runs without them.

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your own values
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

The default dev database is a local SQLite file, so it runs with no Postgres setup. Point `DATABASE_URL` at Postgres for a production-like environment.

## Notes

- Sheets and OCR require a Google service-account key and a Gemini key; both are read from environment variables and never committed
- The confidence threshold, session expiry, and remember-me duration are all configurable
- Frontend flow state persists in localStorage so a driver can resume a half-finished shift (e.g. after the QR scan but before submitting)