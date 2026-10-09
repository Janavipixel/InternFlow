
import os
import smtplib
import requests

from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from AI.pipeline import search_and_process_internships


# =========================================
# LOAD ENVIRONMENT VARIABLES
# =========================================

load_dotenv("AI/.env")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RENDER_BACKEND_URL = (
    os.getenv("RENDER_BACKEND_URL") or ""
).rstrip("/")
AUTOMATION_TOKEN = os.getenv("AUTOMATION_TOKEN")


# =========================================
# GET STUDENTS FROM RENDER
# =========================================

def get_students():

    if not RENDER_BACKEND_URL:
        print("ERROR: RENDER_BACKEND_URL is not configured.")
        return []

    if not AUTOMATION_TOKEN:
        print("ERROR: AUTOMATION_TOKEN is not configured.")
        return []

    try:
        response = requests.get(
            f"{RENDER_BACKEND_URL}/automation/students",
            headers={
                "X-Automation-Token": AUTOMATION_TOKEN
            },
            timeout=60
        )

        print("Render response status:", response.status_code)

        if response.status_code != 200:
            print("Failed to fetch students from Render:")
            print(response.text)
            return []

        students = response.json()

        if not isinstance(students, list):
            print("ERROR: Render returned an unexpected response.")
            return []

        print("Students received from Render:", len(students))
        return students

    except Exception as error:
        print("Error connecting to Render:", error)
        return []


# =========================================
# PARSE SKILLS / LOCATIONS
# =========================================

def parse_skills(value):

    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return []


# =========================================
# PARSE DEADLINE
# =========================================

def parse_deadline(deadline):

    if not deadline:
        return None

    if isinstance(deadline, datetime):
        return deadline.date()

    if isinstance(deadline, date):
        return deadline

    deadline_text = str(deadline).strip()

    if deadline_text.lower() in {
        "n/a",
        "na",
        "none",
        "unknown",
        "not listed",
        "not specified",
        "not available",
        "null",
        ""
    }:
        return None

    # Handle standard YYYY-MM-DD and ISO datetime values.
    try:
        return date.fromisoformat(deadline_text[:10])
    except ValueError:
        pass

    # Handle a few other common date formats.
    for date_format in (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d, %Y",
        "%B %d, %Y"
    ):
        try:
            return datetime.strptime(
                deadline_text,
                date_format
            ).date()
        except ValueError:
            continue

    # An unrecognized date is unknown, not automatically expired.
    return None


# =========================================
# CHECK EMAIL FREQUENCY
# =========================================

def should_send_email(student):

    frequency = (
        student.get("email_frequency") or "Daily"
    ).strip().lower()

    last_sent = student.get("last_email_sent")

    if not last_sent:
        return True

    try:
        last_sent_text = str(last_sent).strip()

        # Support dates and ISO timestamps.
        try:
            last_sent_date = datetime.fromisoformat(
                last_sent_text.replace("Z", "+00:00")
            ).date()
        except ValueError:
            last_sent_date = datetime.strptime(
                last_sent_text[:10],
                "%Y-%m-%d"
            ).date()

    except (ValueError, TypeError):
        print("Could not parse last email date; email is due.")
        return True

    days_since_last_email = (
        date.today() - last_sent_date
    ).days

    if frequency == "daily":
        return days_since_last_email >= 1

    if frequency == "weekly":
        return days_since_last_email >= 7

    return True


# =========================================
# SELECT INTERNSHIPS FOR EMAIL
# =========================================

def get_email_internships(results):

    today = date.today()
    selected = []

    for internship in results:

        if not isinstance(internship, dict):
            continue

        deadline = internship.get("deadline")
        deadline_date = parse_deadline(deadline)

        # Exclude internships with a known expired deadline.
        if deadline_date and deadline_date < today:
            print(
                "Skipped expired internship:",
                internship.get("company", "Unknown"),
                internship.get("role", "Unknown"),
                deadline
            )
            continue

        internship_copy = dict(internship)

        if deadline_date:
            internship_copy["deadline_display"] = (
                deadline_date.isoformat()
            )
            internship_copy["days_left"] = (
                deadline_date - today
            ).days
        else:
            internship_copy["deadline_display"] = (
                "Not listed — check the application page"
            )
            internship_copy["days_left"] = None

        selected.append(internship_copy)

    return selected


# =========================================
# SEND EMAIL
# =========================================

def send_email(student, internships):

    if not internships:
        print("No internships available for email.")
        return False

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("ERROR: Email credentials are not configured.")
        return False

    recipient = student.get("email")

    if not recipient:
        print("ERROR: Student email address is missing.")
        return False

    body = []

    body.append(
        f"Hi {student.get('name') or 'Student'},"
    )
    body.append("")
    body.append(
        "Here are the internship opportunities matching "
        "your saved preferences."
    )
    body.append("")
    body.append(
        f"We found {len(internships)} relevant opportunity/"
        "opportunities for you."
    )
    body.append("")
    body.append(
        "Listings without a published deadline are included too."
    )
    body.append("")

    for index, internship in enumerate(internships, start=1):

        body.append(f"INTERNSHIP {index}")
        body.append("-" * 35)

        body.append(
            f"Company: {internship.get('company') or 'N/A'}"
        )
        body.append(
            f"Role: {internship.get('role') or 'N/A'}"
        )
        body.append(
            f"Location: {internship.get('location') or 'N/A'}"
        )
        body.append(
            f"Stipend: {internship.get('stipend') or 'Not listed'}"
        )
        body.append(
            f"Deadline: {internship.get('deadline_display', 'Not listed')}"
        )

        days_left = internship.get("days_left")

        if days_left is None:
            body.append("Days left: Unknown")
        elif days_left == 0:
            body.append("Days left: Deadline is today")
        else:
            body.append(f"Days left: {days_left}")

        match = internship.get("match_percentage")

        if match is not None:
            body.append(f"Preference match: {match}%")
        else:
            body.append("Preference match: N/A")

        matched_skills = parse_skills(
            internship.get("matched_skills")
        )

        if matched_skills:
            body.append(
                "Matched skills: " + ", ".join(matched_skills)
            )

        application_url = (
            internship.get("application_url")
            or internship.get("application_link")
            or internship.get("source_url")
        )

        body.append(
            f"Application: {application_url or 'Not available'}"
        )
        body.append("")

    body.append("=" * 40)
    body.append(
        "Important: Please check the application page to confirm "
        "that the internship is still open and verify its deadline."
    )
    body.append("")
    body.append(
        "This email was automatically generated by InternFlow."
    )

    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
    message["To"] = recipient
    message["Subject"] = "InternFlow - Your Internship Opportunities"

    message.attach(
        MIMEText("\n".join(body), "plain", "utf-8")
    )

    try:
        print(f"Sending email to {recipient}...")

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=60
        ) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.send_message(message)

        print(f"Email sent successfully to {recipient}")
        return True

    except Exception as error:
        print(f"Failed to send email to {recipient}: {error}")
        return False


# =========================================
# UPDATE LAST EMAIL SENT ON RENDER
# =========================================

def update_last_email_sent(student_id):

    if not RENDER_BACKEND_URL or not AUTOMATION_TOKEN:
        print("ERROR: Render URL or automation token is missing.")
        return False

    try:
        response = requests.put(
            f"{RENDER_BACKEND_URL}/automation/email-sent/{student_id}",
            headers={
                "X-Automation-Token": AUTOMATION_TOKEN
            },
            timeout=60
        )

        if response.status_code != 200:
            print(
                "Failed to update last email date:",
                response.status_code,
                response.text
            )
            return False

        print(
            f"Last email date updated on Render "
            f"for student ID {student_id}."
        )
        return True

    except Exception as error:
        print("Error updating email date on Render:", error)
        return False


# =========================================
# PROCESS ONE STUDENT
# =========================================

def process_student(student):

    print()
    print("=" * 40)
    print(f"Checking {student.get('email')}")
    print("=" * 40)

    print(
        "Email frequency:",
        student.get("email_frequency")
    )
    print(
        "Deadline preference:",
        student.get("deadline_preference")
    )

    if not should_send_email(student):
        print("Email not due yet.")
        return

    student_skills = parse_skills(
        student.get("student_skills")
    )

    preferred_domain = (
        student.get("preferred_domain") or ""
    ).strip()

    locations = parse_skills(
        student.get("locations")
    )

    minimum_stipend = (
        student.get("minimum_stipend") or 0
    )

    if not student_skills:
        print("No student skills found.")
        return

    if not preferred_domain:
        print("No preferred domain found.")
        return

    if not locations:
        print("No preferred location found.")
        return

    all_results = []

    for location in locations:

        print(f"Searching internships for location: {location}")

        try:
            results = search_and_process_internships(
                student_skills,
                preferred_domain,
                location,
                minimum_stipend
            )

            if results:
                all_results.extend(results)

        except Exception as error:
            print(
                f"Pipeline error for {student.get('email')}: {error}"
            )

    # Remove duplicates across different location searches.
    unique_results = []
    seen = set()

    for internship in all_results:

        key = (
            str(internship.get("company", "")).strip().lower(),
            str(internship.get("role", "")).strip().lower(),
            str(internship.get("location", "")).strip().lower()
        )

        if key in seen:
            continue

        seen.add(key)
        unique_results.append(internship)

    print(
        f"Found {len(unique_results)} matching internship(s) "
        "before deadline filtering."
    )

    # Include all relevant results, not just deadlines within
    # the selected 3/7/14/30-day range.
    # Keep entries with no known deadline; exclude known expired ones.
    email_internships = get_email_internships(unique_results)

    print(
        f"{len(email_internships)} internship(s) selected for email."
    )

    if not email_internships:
        print(
            f"No eligible internships to email to "
            f"{student.get('email')}."
        )
        return

    sent = send_email(
        student,
        email_internships
    )

    if sent:
        student_id = student.get("id")

        if student_id is not None:
            update_last_email_sent(student_id)
        else:
            print(
                "WARNING: Email sent, but student ID is missing; "
                "last email date could not be updated."
            )


# =========================================
# MAIN
# =========================================

def main():

    print()
    print("=" * 40)
    print("InternFlow Internship Email Automation")
    print("=" * 40)
    print()

    if not EMAIL_ADDRESS:
        print("ERROR: EMAIL_ADDRESS is not configured.")
        return

    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_PASSWORD is not configured.")
        return

    students = get_students()

    print(f"Found {len(students)} student(s).")

    for student in students:
        try:
            process_student(student)
        except Exception as error:
            print(
                f"Unexpected error while processing "
                f"{student.get('email', 'unknown student')}: {error}"
            )

    print()
    print("=" * 40)
    print("Automation completed.")
    print("=" * 40)


# =========================================
# START PROGRAM
# =========================================

if __name__ == "__main__":
    main()
