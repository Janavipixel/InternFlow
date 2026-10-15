# InternFlow — Personalized Internship Discovery & Automation Platform
[🌐 View InternFlow Live on Render](https://intern-flow-ckh9.onrender.com/)

**Discover relevant internships. Track opportunities. Receive personalized email briefs.**

InternFlow is an intelligent, web-based internship discovery and dispatch platform designed to connect students with verified internship openings tailored to their specific technical skills, domain, location, and stipend expectations.

---

## 📌 Problem Statement

Students frequently waste hours navigating fragmented job portals, news blogs, and expired listings while struggling to identify genuine openings that match their technical proficiencies. Crucial deadlines are easily overlooked, and students often apply without knowing whether their skills align with the company's requirements.

InternFlow solves this by automating:
1. **Targeted Web Discovery:** Real-time web search across company career portals using Tavily.
2. **AI & Deterministic Extraction:** Structured parsing via Google Gemini API with fallback to deterministic pattern extraction.
3. **Smart Skill Matching:** Boundary-safe token matching distinguishing distinct languages (`C`, `C++`, `C#`, `Java`, `JavaScript`) with case normalization and deduplication.
4. **Actionable Opportunity Verification:** Active checks for application URL reachability, dead links, soft 404s, and anti-bot challenges.
5. **Personalized Email Delivery:** Automated daily/weekly email briefs with delivery tracking, audit logging, and duplicate prevention.

---

## 🏗 System Architecture & Data Flow

```text
Student (Web UI / Preferences)
           │
           ▼
     Flask Backend (Render)
     ├── Endpoints: /save-preferences, /preferences, /search-internships
     └── SQLite Storage: internflow.db (WAL mode)
           │
           ├── Web Discovery (Tavily API)
           ├── AI Information Extraction (Gemini 2.5 Flash / Lite / Latest)
           ├── Deterministic Fallback Engine (Structured Text & Regex Parsing)
           ├── Opportunity Verification (Anti-bot detection, status validation)
           └── Skill Matching Engine (Normalized tokens, canonical display)
           │
           ▼
Scheduled GitHub Actions Workflow (04:00 UTC / Manual Trigger)
     ├── Dual-Source Sync (Render API + Local DB fallback)
     ├── Frequency & Deadline Filtering
     ├── Safe SMTP Dispatch (Gmail SSL with bounded retries)
     ├── Idempotent Delivery Tracking (email_logs table)
     └── Rich Job Summary (GitHub Actions Step Summary markdown)
```

---

## ⚙️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Modern JavaScript | Single-page responsive interface with dark glassmorphism aesthetic |
| **Backend API** | Python 3.12+, Flask, Flask-CORS, Gunicorn | High-performance RESTful API with SQLite WAL persistence |
| **AI Extraction** | Google Gemini API (`google-genai` SDK) | Structured JSON parsing with cascade across Gemini 2.5 Flash models |
| **Web Search** | Tavily Search API (`tavily-python`) | Direct career portal discovery without search aggregate clutter |
| **Database** | SQLite3 with WAL journal mode | Tables for preferences, internships, and immutable email audit logs |
| **Email Dispatch** | Python `smtplib` (SSL Port 465) | Personalized plain-text and HTML briefs with delivery diagnosis |
| **CI/CD & Automation** | GitHub Actions | Cron-scheduled execution with summary reporting and secret management |
| **Hosting** | Render Web Service | Production cloud deployment running Gunicorn |
| **Test Suite** | Pytest | 53 unit and integration tests with mocks for external services |

---

## 🗄 Database Schema

The database (`internflow.db`) automatically initializes all tables and indexes on application or automation startup:

### 1. `student_preferences`
Stores student profiles, required criteria, and last email dispatch timestamp:
- `id`: Primary key
- `name`: Student's name
- `email`: Student's unique email address (indexed)
- `student_skills`: Comma-separated list of normalized skills
- `preferred_domain`: Chosen domain (e.g., Cybersecurity, Software Engineering)
- `locations`: Comma-separated list of cities or Remote/Anywhere in India
- `minimum_stipend`: Integer minimum monthly amount in ₹
- `maximum_duration`: Maximum internship duration (e.g., 3 months, 6 months)
- `payment_type`: Paid, Unpaid, or Any
- `work_mode`: In-Office, Remote, or Hybrid
- `study_year`: Academic year
- `availability`: Immediate or specific timeline
- `deadline_preference`: Minimum notice before application close
- `company_preference`: Startup, Mid-size, MNC, etc.
- `email_frequency`: Daily or Weekly
- `last_email_sent`: ISO Date string of last successful email dispatch
- `updated_at`: Timestamp of latest modification

### 2. `internships`
Catalog of discovered and manually added internship opportunities:
- `id`: Primary key
- `company`, `role`, `location`: Core identifying details (indexed together)
- `skills`: Canonical comma-separated required skills
- `stipend`: Freeform text or normalized salary
- `deadline`: Normalized `YYYY-MM-DD` date
- `eligibility`: Eligibility requirements
- `application_link`: Verified direct application URL
- `match_percentage`: Calculated match percentage against student criteria
- `status`: Application status (`Not Applied`, `Applied`, `Interviewing`, `Saved`)
- `saved`: Integer flag (1 if saved)
- `created_at`: Record creation timestamp

### 3. `email_logs`
Immutable audit log tracking every delivery attempt:
- `id`: Primary key
- `workflow_run_id`: GitHub Actions run ID or local timestamp
- `timestamp_utc`: Dispatch timestamp in UTC
- `student_id`: Student foreign key
- `recipient_email_masked`: Privacy-safe masked email (e.g., `ja***@example.com`)
- `eligible_internships_count`: Count of opportunities included
- `attempted`: Integer flag (1 if dispatch was attempted)
- `status`: Outcome category (`accepted_by_provider`, `failed`, `skipped_already_sent`, `skipped_no_matching_internships`, `skipped_incomplete_preferences`)
- `provider_status_code`: SMTP response code (e.g., `250_ACCEPTED`, `535_AUTH_FAIL`)
- `attempt_count`: Number of retry attempts made
- `error_category`: Sanitized error description

---

## 📡 Backend REST API

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the single-page frontend application (`index.html`) |
| `GET` | `/health` | Service health status and database connectivity check |
| `POST` | `/save-preferences` | Creates or updates a student profile with skill deduplication |
| `GET` | `/preferences?email=<email>` | Retrieves a student's profile across sessions and devices |
| `POST` | `/search-internships` | Initiates real-time Tavily search + Gemini extraction + skill matching |
| `GET` | `/internships` | Returns all cataloged internships ordered by recent additions |
| `POST` | `/internships` | Adds an internship record manually |
| `GET` | `/saved-internships` | Returns bookmarked/saved internships |
| `PUT` | `/internships/<id>/status` | Updates application tracking status (`Applied`, `Rejected`, etc.) |
| `PUT` | `/internships/<id>/save` | Toggles bookmark/saved state |
| `GET` | `/internships/deadlines` | Returns internships with deadlines closing within 7 days |
| `GET` | `/automation/students` | **Protected:** Secure sync endpoint for GitHub Actions automation |
| `PUT` | `/automation/email-sent/<id>` | **Protected:** Updates student's `last_email_sent` timestamp |

*Protected endpoints require header `X-Automation-Token: <AUTOMATION_TOKEN>`.*

---

## 🧠 Skill Matching & Boundary Safety

InternFlow uses boundary-safe regex pattern matching to ensure zero false-positive matches:
- **Programming Language Distinctions:** `C`, `C++`, and `C#` are evaluated independently. The letter `C` will never match inside words like `cybersecurity`, `cloud`, `react`, or `css`.
- **Language Boundaries:** `Java` does not match `JavaScript`. `Go` does not match `Django` or `Algorithms`. `SQL` does not match `NoSQL`.
- **Token Normalization:** Case variants like `C` and `c`, or `Python` and `python` are normalized to identical canonical tokens.
- **Alias Resolution:** Common abbreviations (`js` ➔ `JavaScript`, `k8s` ➔ `Kubernetes`, `py` ➔ `Python`, `node` ➔ `Node.js`) map to canonical display names.
- **Accurate Mathematical Percentages:** Denominator is strictly the count of unique required skills. Missing and matched skills are cleanly separated.

---

## 📬 Truthful Email Automation

The email engine in `automation.py` guarantees:
1. **Truthful Outcome Reporting:** An email is only marked `accepted_by_provider` if the SMTP server returns a `250` OK status.
2. **Frequency Enforcement:** Respects `Daily` or `Weekly` student preferences, preventing unwanted email floods.
3. **Safe Test Mode:** Setting `AUTOMATION_TEST_MODE=true` ensures emails are routed strictly to `TEST_EMAIL_RECIPIENT` (or dry-run if unset). Real users are never emailed accidentally during testing.
4. **Bounded Retries:** Exponential backoff with jitter on transient SMTP connection timeouts (up to 2 retries). Fatal authentication or bad recipient errors fail immediately without retry storms.
5. **GitHub Step Summary:** Generates a live markdown table on GitHub Actions showing evaluated, attempted, accepted, failed, and skipped statistics.

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/Janavipixel/InternFlow.git
cd InternFlow/InternFlow
```

### 3. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Populate your API keys and credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
TAVILY_API_KEY=your_tavily_api_key_here
EMAIL_ADDRESS=your_sender_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
RENDER_BACKEND_URL=https://intern-flow-ckh9.onrender.com
AUTOMATION_TOKEN=your_secure_automation_token_here
DATABASE_PATH=internflow.db
AUTOMATION_TEST_MODE=true
TEST_EMAIL_RECIPIENT=your_own_email@gmail.com
```

### 6. Run the Backend Server
```bash
python backend.py
```
Open your browser at `http://localhost:5000`.

### 7. Run the Email Automation Locally
```bash
# In safe test mode (redirects to TEST_EMAIL_RECIPIENT)
python automation.py
```

---

## 🧪 Automated Test Suite

InternFlow includes 53 automated unit and integration tests covering all critical components:

```bash
pytest
```

### Test Coverage Highlights:
- **`tests/test_matching.py`:** Skill tokenization, language distinction (`C` vs `C++` vs `CSS`), alias normalization, deduplication, and percentage accuracy.
- **`tests/test_pipeline.py`:** Unwanted page filtering, boundary-safe skill extraction, location parsing, stipend parsing, deadline normalization, and duplicate removal.
- **`tests/test_verify_application.py`:** Reachability, anti-bot challenge detection (Cloudflare/PerimeterX), soft 404 detection, and network error handling.
- **`tests/test_stipend.py`:** Currency symbols, 'k' multipliers (e.g. ₹20k ➔ 20000), comma numbers, and duration rejection.
- **`tests/test_backend.py`:** Health checks, student preferences CRUD, cross-session `/preferences` retrieval, email automation status inspection (`/student/email-status`), on-demand test dispatch (`/automation/trigger-test`), and token authentication on automation routes.
- **`tests/test_database.py`:** Table creation, schema migrations, WAL journal mode, and privacy-safe email log masking.
- **`tests/test_gemini_client.py`:** Missing key detection, successful mocked generation, and quota exhaustion graceful fallback.
- **`tests/test_automation.py`:** Frequency filtering, expired listing exclusion, test mode redirection, SMTP error handling, and GitHub Actions summary generation.

---

## ☁️ Deployment Guide

### Render Web Service (Backend)
1. Link your GitHub repository to Render as a **Web Service**.
2. **Environment:** Python 3.12+
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `gunicorn backend:app`
5. **Environment Variables:**
   - `GEMINI_API_KEY`: Your Gemini API key
   - `TAVILY_API_KEY`: Your Tavily API key
   - `AUTOMATION_TOKEN`: A strong secret shared with GitHub Actions
   - `FLASK_DEBUG`: `false`

### GitHub Actions (Scheduled Automation)
The workflow runs automatically at `04:00 UTC` daily via `.github/workflows/deadline_reminder.yml`, or can be triggered manually via `workflow_dispatch`.

Configure the following in **GitHub Repository ➔ Settings ➔ Secrets and variables ➔ Actions**:
- `EMAIL_ADDRESS`: Dispatch sender email address
- `EMAIL_PASSWORD`: Gmail App Password (16 characters)
- `RENDER_BACKEND_URL`: `https://intern-flow-ckh9.onrender.com`
- `AUTOMATION_TOKEN`: Matching secret configured on Render
- `TAVILY_API_KEY`: Your Tavily API key
- `GEMINI_API_KEY`: Your Gemini API key
- *(Optional)* `TEST_EMAIL_RECIPIENT`: Destination address for test runs
- *(Optional)* `DATABASE_B64`: Base64 encoded snapshot of `internflow.db` for offline backup

---

## 🔒 Security Best Practices

- **Zero Secrets Committed:** All credentials are loaded strictly from environment variables or GitHub Secrets. `.gitignore` protects `.env` and `AI/.env`.
- **Privacy Masking:** Email addresses recorded in `email_logs` are automatically masked (e.g., `al***@gmail.com`).
- **Endpoint Security:** `/automation/students` and `/automation/email-sent` require strong token authentication via the `X-Automation-Token` header.
- **Sanitized HTML:** User-supplied inputs and search text are safely escaped before frontend DOM insertion.
- **Ephemeral Runner Safety:** GitHub Actions never prints secrets, tokens, or email passwords in console logs.

---

## 🎬 Complete Demonstration Guide (Viva / Presentation)

Follow this 9-step demonstration flow to present InternFlow to professors, reviewers, or team members:

1. **Start the Application Locally:**
   Run `python backend.py` in your terminal and open `http://localhost:5000` in your browser. Show the Landing & Login screen.
2. **Configure Student Preferences:**
   Enter a student's name, email, skills (`Python, SQL, Flask`), preferred domain (`Software Engineering`), location (`Remote`, `Mumbai`), and minimum stipend (`₹15,000`). Submit the form.
3. **Verify Database Persistence:**
   Show that refreshing the page or logging out and logging back in immediately reloads the student's saved preferences from SQLite via `GET /preferences?email=...`.
4. **Trigger Instant AI-Assisted Discovery:**
   View the live search execution. Show how Tavily queries live web listings and Google Gemini extracts structured metadata (stipend, duration, deadlines, application links).
5. **Explain the Matching Engine & Ranking:**
   Point out how match percentages are calculated. Show the color-coded **Matched Skills** (green) and **Missing Skills** (amber) chips, and demonstrate how opportunities with higher matches appear at the top.
6. **Demonstrate Active Application Verification:**
   Click the **View & Apply →** button to show that the opportunity leads directly to an active, verified application portal.
7. **Test On-Demand Email Dispatch:**
   In the **Personalized Email Automation** card, click **✉️ Send Test Brief to Inbox**. Watch the live status transition (`⏳ Dispatching brief...` ➔ `✅ Success!`). Open the recipient inbox and show the personalized HTML brief delivered via Gmail SMTP.
8. **Show the Immutable Audit Log:**
   Open SQLite (`sqlite3 internflow.db`) and run `SELECT * FROM email_logs;`. Show how the email delivery attempt was recorded with masked email addresses, status codes, and timestamps.
9. **Explain the Scheduled GitHub Actions Pipeline:**
   Open `.github/workflows/deadline_reminder.yml` and show how the platform runs unattended every day at 04:00 UTC to evaluate all students and dispatch alerts before deadlines expire.

---

## 📄 License

Developed for the InternFlow internship discovery platform.
