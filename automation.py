import os
import sys
import time
import smtplib
import socket
import requests
from datetime import date, datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from AI.pipeline import search_and_process_internships
from database import create_database, get_db_connection, record_email_log, get_db_matched_internships

# Ensure local tables and schema exist
create_database()

# =========================================
# LOAD CONFIGURATION & SECRETS
# =========================================

# Load AI/.env first, then root .env if present
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "AI", ".env"))
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

RENDER_BACKEND_URL = (os.getenv("RENDER_BACKEND_URL") or "").rstrip("/")
AUTOMATION_TOKEN = os.getenv("AUTOMATION_TOKEN")

# Safe Testing Mode
AUTOMATION_TEST_MODE = os.getenv("AUTOMATION_TEST_MODE", "false").lower() in ("true", "1", "yes")
TEST_EMAIL_RECIPIENT = os.getenv("TEST_EMAIL_RECIPIENT")

WORKFLOW_RUN_ID = (
    os.getenv("GITHUB_RUN_ID")
    or os.getenv("GITHUB_RUN_NUMBER")
    or f"local-{int(time.time())}"
)


# =========================================
# STUDENT RETRIEVAL (RENDER + LOCAL FALLBACK)
# =========================================

def get_students_from_render():
    """
    Attempts to fetch student preferences from the hosted Render backend with retries.
    """
    if not RENDER_BACKEND_URL or not AUTOMATION_TOKEN:
        return None

    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            print(f"[Automation] Fetching students from Render (attempt {attempt + 1}/{max_attempts})...")
            response = requests.get(
                f"{RENDER_BACKEND_URL}/automation/students",
                headers={"X-Automation-Token": AUTOMATION_TOKEN},
                timeout=6,
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"[Automation] Successfully received {len(data)} student(s) from Render.")
                    return data
                print("[Automation] Render returned non-list data.")
                return None
            elif response.status_code == 401:
                print("[Automation] Render returned 401 Unauthorized (check AUTOMATION_TOKEN).")
                return None
            else:
                print(f"[Automation] Render returned status {response.status_code}: {response.text[:200]}")
        except (requests.RequestException, Exception) as err:
            print(f"[Automation] Failed to connect to Render: {err}")

        if attempt < max_attempts - 1:
            time.sleep(5)

    return None


def get_students_from_local_db():
    """
    Retrieves student preferences directly from the local SQLite database.
    """
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM student_preferences").fetchall()
        conn.close()
        students = [dict(r) for r in rows]
        print(f"[Automation] Retrieved {len(students)} student(s) from local database.")
        return students
    except Exception as err:
        print(f"[Automation] Error reading local database: {err}")
        return []


def get_students():
    """
    Dual-source student retrieval:
    1. Try Render backend (ensuring cloud freshness).
    2. Fall back to local SQLite database if Render is asleep, down, or unconfigured.
    """
    students = get_students_from_render()
    if students is not None and len(students) > 0:
        return students

    print("[Automation] Using local database fallback for student preferences.")
    return get_students_from_local_db()


# =========================================
# PREFERENCE PARSING
# =========================================

def parse_skills(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def parse_deadline(deadline):
    if not deadline:
        return None
    if isinstance(deadline, datetime):
        return deadline.date()
    if isinstance(deadline, date):
        return deadline

    text = str(deadline).strip()
    if text.lower() in {"n/a", "na", "none", "unknown", "not listed", "not specified", "null", ""}:
        return None

    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def should_send_email(student):
    frequency = (student.get("email_frequency") or "Daily").strip().lower()
    if frequency in ("never", "paused", "none", "off", "pause", "stop"):
        return False

    last_sent = student.get("last_email_sent")

    if not last_sent:
        return True

    try:
        last_sent_str = str(last_sent).strip()
        try:
            last_date = datetime.fromisoformat(last_sent_str.replace("Z", "+00:00")).date()
        except ValueError:
            last_date = datetime.strptime(last_sent_str[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return True

    days = (date.today() - last_date).days
    if frequency == "daily":
        return days >= 1
    if "3" in frequency:
        return days >= 3
    if frequency == "weekly":
        return days >= 7
    return True


# =========================================
# INTERNSHIP SELECTION
# =========================================

def get_email_internships(results):
    today = date.today()
    selected = []

    for item in results:
        if not isinstance(item, dict):
            continue

        deadline = item.get("deadline")
        deadline_date = parse_deadline(deadline)

        # Discard expired internships
        if deadline_date and deadline_date < today:
            continue

        copy = dict(item)
        if deadline_date:
            copy["deadline_display"] = deadline_date.isoformat()
            copy["days_left"] = (deadline_date - today).days
        else:
            copy["deadline_display"] = "Open / Rolling (Actively Hiring)"
            copy["days_left"] = None

        selected.append(copy)

    return selected


# =========================================
# SEND EMAIL WITH RETRIES & AUDIT STATUS
# =========================================

def send_email(student, internships, max_retries=2):
    """
    Sends personalized internship brief with:
    - Safe test recipient override if in TEST_MODE
    - Bounded exponential backoff for transient network issues
    - No retries on fatal authentication or recipient errors
    - Returns: (success: bool, status_code: str, error_category: str)
    """
    if not internships:
        return False, "SKIPPED_EMPTY", "No eligible internships"

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return False, "AUTH_MISSING", "EMAIL_ADDRESS or EMAIL_PASSWORD not configured"

    actual_recipient = student.get("email")
    if not actual_recipient:
        return False, "INVALID_RECIPIENT", "Missing recipient email"

    # In test mode, redirect to test recipient or prevent sending
    target_recipient = actual_recipient
    if AUTOMATION_TEST_MODE:
        if TEST_EMAIL_RECIPIENT:
            print(f"[TEST MODE] Redirecting email from {actual_recipient} to TEST recipient: {TEST_EMAIL_RECIPIENT}")
            target_recipient = TEST_EMAIL_RECIPIENT
        else:
            print(f"[TEST MODE] Dry run: TEST_EMAIL_RECIPIENT not set. Skipping real dispatch.")
            return True, "TEST_DRY_RUN", None

    body = [
        f"Hi {student.get('name') or 'Student'},",
        "",
        "Here are the latest internship opportunities matching your preferences.",
        f"We found {len(internships)} relevant opportunity/opportunities for you.",
        "",
        "Listings with rolling deadlines are included so you can apply early before spots fill.",
        "",
    ]

    for index, item in enumerate(internships, start=1):
        body.append(f"INTERNSHIP {index}")
        body.append("-" * 35)
        body.append(f"Company: {item.get('company') or 'Company provided on job listing'}")
        body.append(f"Role: {item.get('role') or 'Internship'}")
        body.append(f"Location: {item.get('location') or 'Specified in application link'}")
        body.append(f"Stipend: {item.get('stipend') or 'Disclosed upon application / Competitive'}")

        deadline_date = parse_deadline(item.get("deadline"))
        days_left = item.get("days_left")
        if deadline_date and days_left is not None:
            if days_left == 0:
                body.append(f"Application Deadline: {deadline_date.isoformat()} (Closing Today!)")
            else:
                body.append(f"Application Deadline: {deadline_date.isoformat()} ({days_left} day(s) remaining)")
        else:
            body.append("Application Deadline: Open / Rolling (Applications currently accepted — apply early)")

        if item.get("eligibility"):
            body.append(f"Eligibility: {item.get('eligibility')}")

        if item.get("description"):
            body.append(f"Role Overview: {item.get('description')}")

        match = item.get("match_percentage")
        body.append(f"Preference match: {match}%" if match is not None else "Preference match: N/A")

        matched_skills = parse_skills(item.get("matched_skills"))
        if matched_skills:
            body.append(f"Matched skills: {', '.join(matched_skills)}")

        missing_skills = parse_skills(item.get("missing_skills"))
        if missing_skills:
            body.append(f"Skills to learn: {', '.join(missing_skills)}")

        app_url = (
            item.get("application_url")
            or item.get("application_link")
            or item.get("source_url")
            or "Not available"
        )
        body.append(f"Application Link: {app_url}")
        body.append("")

    body.append("=" * 40)
    body.append("Important: Please check the application page to confirm current opening status.")
    body.append("")
    body.append("This email was automatically generated by InternFlow.")

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = target_recipient
    msg["Subject"] = "InternFlow - Your Internship Opportunities"
    msg.attach(MIMEText("\n".join(body), "plain", "utf-8"))

    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            print(f"[Automation] Sending email to {target_recipient} (attempt {attempt})...")
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            print(f"[Automation] Email accepted by SMTP provider for {target_recipient}")
            return True, "250_ACCEPTED", None

        except smtplib.SMTPAuthenticationError as err:
            print(f"[Automation] SMTP Authentication failed: {err}")
            return False, "535_AUTH_FAIL", "Authentication failure"

        except smtplib.SMTPRecipientsRefused as err:
            print(f"[Automation] SMTP Recipient refused: {err}")
            return False, "550_RECIPIENT_REFUSED", "Invalid recipient"

        except (smtplib.SMTPServerDisconnected, socket.timeout, smtplib.SMTPException) as err:
            print(f"[Automation] Transient SMTP error on attempt {attempt}: {err}")
            if attempt <= max_retries:
                time.sleep(2 * attempt)
            else:
                return False, "SMTP_ERROR", str(err)
        except Exception as err:
            print(f"[Automation] Unexpected error during email send: {err}")
            return False, "UNKNOWN_ERROR", str(err)

    return False, "MAX_RETRIES_EXCEEDED", "Exceeded maximum retries"


# =========================================
# STATE SYNCHRONIZATION
# =========================================

def update_last_email_sent(student_id):
    """
    Updates the last_email_sent timestamp in both:
    1. Local SQLite database.
    2. Render backend if configured.
    """
    today_iso = date.today().isoformat()

    # 1. Update local SQLite DB
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE student_preferences SET last_email_sent = ? WHERE id = ?",
            (today_iso, student_id),
        )
        conn.commit()
        conn.close()
        print(f"[Automation] Updated local last_email_sent for student ID {student_id}")
    except Exception as err:
        print(f"[Automation] Error updating local database: {err}")

    # 2. Update Render backend if configured (bounded timeout so sleeping free tier never blocks user)
    if RENDER_BACKEND_URL and AUTOMATION_TOKEN:
        try:
            resp = requests.put(
                f"{RENDER_BACKEND_URL}/automation/email-sent/{student_id}",
                headers={"X-Automation-Token": AUTOMATION_TOKEN},
                timeout=3.5,
            )
            if resp.status_code == 200:
                print(f"[Automation] Updated last_email_sent on Render for student ID {student_id}")
            else:
                print(f"[Automation] Render date update note: code {resp.status_code}")
        except Exception as err:
            print(f"[Automation] Note: Render instance idle or unreachable ({err})")


# =========================================
# PROCESS INDIVIDUAL STUDENT
# =========================================

def process_student(student, force=False):
    student_id = student.get("id")
    email = student.get("email")

    print("\n" + "=" * 40)
    print(f"Processing student: {email} (force={force})")
    print("=" * 40)

    if not force and not should_send_email(student):
        print("[Automation] Email not due yet based on frequency.")
        record_email_log(
            student_id=student_id,
            recipient_email=email,
            eligible_internships_count=0,
            attempted=False,
            status="skipped_already_sent",
            workflow_run_id=WORKFLOW_RUN_ID,
            provider_status_code="SKIPPED",
            error_category="Frequency limit",
        )
        return "skipped_already_sent"

    skills = parse_skills(student.get("student_skills"))
    domain = (student.get("preferred_domain") or "").strip()
    locations = parse_skills(student.get("locations"))
    stipend = student.get("minimum_stipend") or 0

    if not skills or not domain or not locations:
        print("[Automation] Incomplete preferences. Skipping.")
        record_email_log(
            student_id=student_id,
            recipient_email=email,
            eligible_internships_count=0,
            attempted=False,
            status="skipped_incomplete_preferences",
            workflow_run_id=WORKFLOW_RUN_ID,
            provider_status_code="SKIPPED",
            error_category="Missing required student criteria",
        )
        return "skipped_incomplete_preferences"

    # 1. First query verified opportunities from database (instant sub-10ms response)
    all_found = []
    try:
        db_matches = get_db_matched_internships(
            student_skills=skills,
            preferred_domain=domain,
            locations=locations,
            minimum_stipend=stipend,
        )
        if db_matches:
            all_found.extend(db_matches)
    except Exception as db_err:
        print(f"[Automation] DB lookup note: {db_err}")

    # 2. If fewer than 2 active matches exist in DB, run targeted search for top locations
    if len(all_found) < 2:
        search_locations = [l for l in locations if l.lower() != "anywhere in india"][:2]
        if not search_locations:
            search_locations = ["Remote"]
        for loc in search_locations:
            print(f"[Automation] Searching {domain} internships in {loc}...")
            try:
                results = search_and_process_internships(
                    student_skills=skills,
                    preferred_domain=domain,
                    location=loc,
                    minimum_stipend=stipend,
                )
                if results:
                    all_found.extend(results)
            except Exception as err:
                print(f"[Automation] Pipeline error for {email} in {loc}: {err}")

    # Deduplicate by company, role, location
    unique = []
    seen = set()
    for item in all_found:
        key = (
            str(item.get("company", "")).strip().lower(),
            str(item.get("role", "")).strip().lower(),
            str(item.get("location", "")).strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    eligible = get_email_internships(unique)
    print(f"[Automation] Found {len(eligible)} eligible internship(s) for email.")

    if not eligible:
        print(f"[Automation] No matching internships found for {email}.")
        record_email_log(
            student_id=student_id,
            recipient_email=email,
            eligible_internships_count=0,
            attempted=False,
            status="skipped_no_matching_internships",
            workflow_run_id=WORKFLOW_RUN_ID,
            provider_status_code="SKIPPED",
            error_category="Zero matches found",
        )
        return "skipped_no_matching_internships"

    # Attempt to send email
    success, status_code, err_msg = send_email(student, eligible)

    final_status = "accepted_by_provider" if success else "failed"
    record_email_log(
        student_id=student_id,
        recipient_email=email,
        eligible_internships_count=len(eligible),
        attempted=True,
        status=final_status,
        workflow_run_id=WORKFLOW_RUN_ID,
        provider_status_code=status_code,
        error_category=err_msg,
    )

    if success:
        if student_id:
            update_last_email_sent(student_id)
        return "accepted_by_provider"
    else:
        return "failed"


def write_github_summary(summary, run_id):
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    try:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(f"## 📬 InternFlow Automation Summary (Run: `{run_id}`)\n\n")
            f.write(f"**Execution Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write("| Metric | Count |\n")
            f.write("| :--- | :--- |\n")
            f.write(f"| **Students Evaluated** | {summary['processed']} |\n")
            f.write(f"| **Emails Attempted** | {summary['attempted']} |\n")
            f.write(f"| **Accepted by Provider** | {summary['accepted']} |\n")
            f.write(f"| **Failed Emails** | {summary['failed']} |\n")
            f.write(f"| *Skipped: Not Due (Frequency)* | {summary['skipped']['already_sent']} |\n")
            f.write(f"| *Skipped: Incomplete Criteria* | {summary['skipped']['incomplete_preferences']} |\n")
            f.write(f"| *Skipped: No Matching Openings* | {summary['skipped']['no_matches']} |\n\n")

            if summary["attempted"] == 0:
                f.write("> ℹ️ **Notice:** No emails were dispatched because no eligible internships matched the active criteria or deadlines for evaluated students.\n\n")
            elif summary["failed"] > 0:
                f.write("> ⚠️ **Warning:** Some email dispatches encountered errors. Please inspect the workflow logs.\n\n")
            else:
                f.write("> ✅ **Success:** All eligible student emails were successfully accepted by the SMTP provider.\n\n")
    except Exception as e:
        print(f"[Automation] Note: Could not write GitHub step summary: {e}")


# =========================================
# MAIN ENTRY POINT
# =========================================

def main():
    print("\n" + "=" * 50)
    print("InternFlow Automation Engine")
    print(f"Run ID: {WORKFLOW_RUN_ID} | Test Mode: {AUTOMATION_TEST_MODE}")
    print("=" * 50 + "\n")

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        if AUTOMATION_TEST_MODE and not TEST_EMAIL_RECIPIENT:
            print("[Automation] WARNING: Running in test mode without real email credentials (dry run only).")
        else:
            print("ERROR: EMAIL_ADDRESS or EMAIL_PASSWORD environment variables missing.")
            sys.exit(1)

    students = get_students()
    if not students:
        print("[Automation] WARNING: No students found to process.")
        print("[Automation] Checked Render and local database. Both returned 0 students.")
        # If no students exist, exit 0 as clean state
        return

    print(f"[Automation] Beginning processing for {len(students)} student(s).\n")

    summary = {
        "processed": len(students),
        "attempted": 0,
        "accepted": 0,
        "failed": 0,
        "skipped": {
            "already_sent": 0,
            "incomplete_preferences": 0,
            "no_matches": 0,
        },
    }

    for student in students:
        outcome = process_student(student)
        if outcome == "accepted_by_provider":
            summary["attempted"] += 1
            summary["accepted"] += 1
        elif outcome == "failed":
            summary["attempted"] += 1
            summary["failed"] += 1
        elif outcome == "skipped_already_sent":
            summary["skipped"]["already_sent"] += 1
        elif outcome == "skipped_incomplete_preferences":
            summary["skipped"]["incomplete_preferences"] += 1
        elif outcome == "skipped_no_matching_internships":
            summary["skipped"]["no_matches"] += 1

    print("\n" + "=" * 50)
    print("AUTOMATION SUMMARY")
    print("=" * 50)
    print(f"Total students evaluated: {summary['processed']}")
    print(f"Emails attempted:        {summary['attempted']}")
    print(f"Accepted by provider:    {summary['accepted']}")
    print(f"Failed emails:           {summary['failed']}")
    print("Skipped reasons:")
    print(f"  - Not due (frequency): {summary['skipped']['already_sent']}")
    print(f"  - Incomplete preferences:{summary['skipped']['incomplete_preferences']}")
    print(f"  - No matching openings:  {summary['skipped']['no_matches']}")
    print("=" * 50 + "\n")

    # Record summary in GitHub Actions UI if running on GitHub
    write_github_summary(summary, WORKFLOW_RUN_ID)

    # If any attempted email failed completely, exit with error code 1 so GitHub Actions reports failure
    if summary["attempted"] > 0 and summary["failed"] > 0:
        print("[Automation] Completed with errors: Some email deliveries failed.")
        sys.exit(1)

    print("[Automation] Completed successfully.")


if __name__ == "__main__":
    main()

