# JobMatch — Job Application Tracker & Resume Matcher

JobMatch gives job seekers one focused place to manage an application pipeline and check whether a resume speaks the language of a role. It combines a clean CRUD tracker with a transparent resume-to-job-description score—without accounts, paid APIs, or a heavyweight ML model.

## Why this project

Applying to many roles creates two related problems: application details scatter across notes and spreadsheets, and resume tailoring becomes guesswork. JobMatch keeps the pipeline visible and surfaces skills or keywords present in a job description but absent from a resume. The score is a prompt for thoughtful editing, not an applicant-tracking-system prediction.

## Features

- Add, edit, filter, and delete job applications
- Track company, role, link, status, date applied, and notes
- View application counts by status and daily activity on a dashboard
- Compare pasted resume text with a job description
- Get a 0–100 match score, matched skills, and missing terms
- Store applications in a persistent SQLite database
- Load realistic sample data for a quick demo
- Use a responsive interface with no frontend build step

## Tech stack

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite through Python's standard `sqlite3` module
- **Frontend:** Jinja templates, plain CSS, and vanilla JavaScript
- **Scoring:** TF-IDF-weighted cosine similarity plus explicit skill coverage
- **Tests:** pytest and Flask's test client

## Project structure

```text
job-tracker-matcher/
├── job_tracker/
│   ├── static/           # CSS and matcher JavaScript
│   ├── templates/        # Jinja page templates
│   ├── __init__.py       # App factory and demo-data command
│   ├── db.py             # SQLite connection and schema
│   ├── matcher.py        # Text scoring and term extraction
│   └── routes.py         # Dashboard, CRUD, and matcher routes
├── tests/                # Route and scoring tests
├── run.py                # Local entry point
├── requirements.txt
└── requirements-dev.txt
```

## Run locally

```bash
git clone https://github.com/Kindeya03/job-tracker-matcher.git
cd job-tracker-matcher
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app run.py run --debug
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The app creates `instance/job_tracker.sqlite` automatically on first run.

To populate the dashboard for a two-minute demo:

```bash
flask --app run.py seed
```

The seed command is intentionally safe to rerun: it does nothing when applications already exist.

## Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

The test suite uses an isolated temporary SQLite database and covers CRUD operations, validation, dashboard rendering, score calculation, missing-skill extraction, and API errors.

## How match scoring works

1. Normalize the job description and resume into meaningful tokens.
2. Build TF-IDF-weighted vectors from the two documents.
3. Calculate cosine similarity to measure their vocabulary alignment.
4. Detect a curated set of common technical skills in both texts.
5. Blend broad similarity (70%) with exact skill coverage (30%).
6. Return up to 12 high-signal terms found in the job description but missing from the resume.

This approach is fast, explainable, deterministic, and dependency-light. It deliberately does not claim to reproduce a company's ATS or judge whether someone is qualified. Missing terms should only be added when they truthfully describe the candidate's experience.

## Design decisions

- **Server-rendered Flask over React:** fewer moving parts makes the app easy to run and demo while still showing clear backend/frontend boundaries.
- **SQLite over in-memory storage:** data survives restarts, the schema is easy to inspect, and setup remains one command.
- **Raw `sqlite3` over an ORM:** the schema and queries stay visible in a small project, which makes data flow easier to discuss in an interview.
- **Local single-user model:** authentication would add complexity without improving the intended local demo. The app factory leaves room to add it later.
- **No resume persistence:** application records are stored, but pasted resume and job-description text are processed for one request and discarded.
- **No chart dependency:** the activity chart is rendered with semantic HTML/CSS, avoiding another download or build step.

## API

The UI sends resume comparisons to one JSON endpoint:

```http
POST /matcher
Content-Type: application/json

{
  "job_description": "We need a Python engineer with Flask and AWS...",
  "resume": "Built Python APIs with Flask and PostgreSQL..."
}
```

```json
{
  "score": 63,
  "matched_skills": ["Python", "Flask"],
  "missing_terms": ["AWS"]
}
```

## For interviews

**Problem it solves:** Job seekers often track applications in one place and tailor resumes somewhere else. JobMatch joins those workflows: it keeps every opportunity and its current status visible, then gives the user a fast, explainable signal about how closely their resume matches a target role.

**Key design decisions:** I used Flask with server-rendered templates to keep the architecture simple and demo-friendly, SQLite for real persistence with zero infrastructure, and a transparent hybrid scorer. The score combines TF-IDF/cosine similarity for overall language alignment with exact skill coverage so the output remains understandable. Resume text is never stored.

**What I would improve with more time:** I would add user accounts and CSRF protection for a hosted multi-user version, database migrations, richer skill extraction for multi-word domain terms, PDF/DOCX resume parsing, saved match history, accessible chart labels, pagination and search, and end-to-end browser tests. I would also calibrate the scoring weights against human-reviewed resume/job pairs rather than presenting them as universal.

**Tech stack:** Python, Flask, SQLite, Jinja, vanilla JavaScript, CSS, and pytest.
