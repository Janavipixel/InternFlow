import os
import sqlite3
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

DATABASE = os.getenv("DATABASE", "internflow.db")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RENDER_BACKEND_URL = os.getenv("RENDER_BACKEND_URL")
AUTOMATION_TOKEN = os.getenv("AUTOMATION_TOKEN")


# =========================================
# DATABASE CONNECTION
# =========================================

def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================
# GET STUDENTS
# =========================================


def get_students():
    if not RENDER_BACKEND_URL:
        print("ERROR: RENDER_BACKEND_URL is not configured.")
        return []

    if not AUTOMATION_TOKEN:
        print("ERROR: AUTOMATION_TOKEN is not configured.")
        return []

    try:
        url = f"{RENDER_BACKEND_URL.rstrip('/')}/automation/students"
        print("Fetching students from Render API...")

        response = requests.get(
            url,
            headers={"X-Automation-Token": AUTOMATION_TOKEN},
            timeout=30
        )

        print("Render API status:", response.status_code)

        if response.status_code != 200:
            print("Render API error:", response.text[:500])
            return []

        students = response.json()

        if not isinstance(students, list):
            print("ERROR: Expected a list from Render API.")
            print("Response type:", type(students).__name__)
            return []

        print("Students returned by Render:", len(students))

        if len(students) == 0:
            print("No student records exist in the database used by Render.")

        return students

    except Exception as error:
        print("Error fetching students:", repr(error))
        return []


# =========================================
# PARSE STUDENT SKILLS
# =========================================

def parse_skills(skills):

    if not skills:
        return []

    if isinstance(skills, list):
        return skills

    return [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]


# =========================================
# CHECK IF EMAIL SHOULD BE SENT
# =========================================

def should_send_email(student):

    frequency = student["email_frequency"]

    last_sent = student["last_email_sent"]

    today = date.today()

    # -------------------------------------
    # No previous email
    # -------------------------------------

    if not last_sent:

        return True

    try:

        last_sent_date = datetime.strptime(
            last_sent,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return True

    days_since_last_email = (
        today - last_sent_date
    ).days

    # -------------------------------------
    # Daily
    # -------------------------------------

    if frequency == "Daily":

        return days_since_last_email >= 1

    # -------------------------------------
    # Weekly
    # -------------------------------------

    if frequency == "Weekly":

        return days_since_last_email >= 7

    # -------------------------------------
    # Default
    # -------------------------------------

    return True


# =========================================
# GET UPCOMING DEADLINES
# =========================================

def get_upcoming_deadlines(results):

    today = date.today()

    last_day = today + timedelta(days=7)

    upcoming = []

    for internship in results:

        deadline = internship.get("deadline")

        if not deadline:

            continue

        try:

            deadline_date = datetime.strptime(
                deadline,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            continue

        # ---------------------------------
        # Deadline must be today → 7 days
        # ---------------------------------

        if today <= deadline_date <= last_day:

            internship_copy = dict(internship)

            internship_copy["days_left"] = (
                deadline_date - today
            ).days

            upcoming.append(internship_copy)

    return upcoming


# =========================================
# SEND EMAIL
# =========================================

def send_email(student, internships):

    if not internships:

        print(
            f"No matching internships for "
            f"{student['email']}."
        )

        return False

    subject = (
        "InternFlow - Internship Deadline Reminder"
    )

    body = []

    body.append(
        f"Hi {student['name'] or 'Student'},"
    )

    body.append("")

    body.append(
        "Here are internship opportunities matching "
        "your preferences and having deadlines within "
        "the next 7 days:"
    )

    body.append("")

    for internship in internships:

        body.append(
            f"Company: {internship.get('company', 'N/A')}"
        )

        body.append(
            f"Role: {internship.get('role', 'N/A')}"
        )

        body.append(
            f"Location: {internship.get('location', 'N/A')}"
        )

        body.append(
            f"Stipend: {internship.get('stipend', 'N/A')}"
        )

        body.append(
            f"Deadline: {internship.get('deadline', 'N/A')}"
        )

        body.append(
            f"Days left: {internship.get('days_left', 'N/A')}"
        )

        body.append(
            f"Match: "
            f"{internship.get('match_percentage', 'N/A')}%"
        )

        matched = internship.get(
            "matched_skills",
            []
        )

        if matched:

            body.append(
                "Matched skills: "
                + ", ".join(matched)
            )

        body.append(
            "Application: "
            + internship.get(
                "application_url",
                "N/A"
            )
        )

        body.append("")

        body.append("------------------------------")

        body.append("")

    body.append(
        "Apply before the deadline!"
    )

    body.append("")

    body.append(
        "This email was automatically generated "
        "by InternFlow."
    )

    message = MIMEMultipart()

    message["From"] = EMAIL_ADDRESS

    message["To"] = student["email"]

    message["Subject"] = subject

    message.attach(
        MIMEText(
            "\n".join(body),
            "plain"
        )
    )

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                EMAIL_ADDRESS,
                EMAIL_PASSWORD
            )

            server.send_message(message)

        print(
            f"Email sent successfully to "
            f"{student['email']}"
        )

        return True

    except Exception as error:

        print(
            f"Failed to send email to "
            f"{student['email']}: {error}"
        )

        return False


# =========================================
# UPDATE LAST EMAIL SENT
# =========================================

def update_last_email_sent(student_id):

    connection = get_db_connection()

    connection.execute("""
        UPDATE student_preferences
        SET last_email_sent = ?
        WHERE id = ?
    """, (
        date.today().isoformat(),
        student_id
    ))

    connection.commit()

    connection.close()


# =========================================
# PROCESS ONE STUDENT
# =========================================

def process_student(student):

    print()

    print("================================")
    print(
        f"Checking {student['email']}"
    )
    print("================================")

    print(
        "Email frequency:",
        student["email_frequency"]
    )

    # -------------------------------------
    # Check frequency
    # -------------------------------------

    if not should_send_email(student):

        print(
            "Email not due yet."
        )

        return

    # -------------------------------------
    # Student preferences
    # -------------------------------------

    student_skills = parse_skills(
        student["student_skills"]
    )

    preferred_domain = (
        student["preferred_domain"]
        or ""
    )

    locations = parse_skills(
        student["locations"]
    )

    minimum_stipend = (
        student["minimum_stipend"]
        or 0
    )

    if not student_skills:

        print(
            "No student skills found."
        )

        return

    if not preferred_domain:

        print(
            "No preferred domain found."
        )

        return

    if not locations:

        print(
            "No preferred location found."
        )

        return

    # -------------------------------------
    # Run AI pipeline
    # -------------------------------------

    all_results = []

    for location in locations:

        print(
            f"Searching internships for "
            f"location: {location}"
        )

        try:

            results = (
                search_and_process_internships(
                    student_skills,
                    preferred_domain,
                    location,
                    minimum_stipend
                )
            )

            if results:

                all_results.extend(results)

        except Exception as error:

            print(
                f"Pipeline error for "
                f"{student['email']}: {error}"
            )

    # -------------------------------------
    # Remove duplicate internships
    # -------------------------------------

    unique_results = []

    seen = set()

    for internship in all_results:

        key = (
            internship.get("company"),
            internship.get("role"),
            internship.get("location")
        )

        if key in seen:

            continue

        seen.add(key)

        unique_results.append(internship)

    # -------------------------------------
    # Deadline filtering
    # -------------------------------------

    upcoming = get_upcoming_deadlines(
        unique_results
    )

    print(
        f"Found {len(unique_results)} "
        f"matching internship(s)."
    )

    print(
        f"{len(upcoming)} have deadlines "
        f"within the next 7 days."
    )

    # -------------------------------------
    # Send email
    # -------------------------------------

    if upcoming:

        sent = send_email(
            student,
            upcoming
        )

        if sent:

            update_last_email_sent(
                student["id"]
            )

    else:

        print(
            f"No upcoming matching deadlines "
            f"for {student['email']}."
        )


# =========================================
# MAIN
# =========================================

def main():

    print()
    print("================================")
    print("InternFlow Deadline Automation")
    print("================================")
    print()

    if not EMAIL_ADDRESS:

        print(
            "ERROR: EMAIL_ADDRESS is not configured."
        )

        return

    if not EMAIL_PASSWORD:

        print(
            "ERROR: EMAIL_PASSWORD is not configured."
        )

        return

    students = get_students()

    print(
        f"Found {len(students)} student(s)."
    )

    for student in students:

        process_student(student)

    print()

    print("================================")
    print("Automation completed.")
    print("================================")


# =========================================
# START
# =========================================

if __name__ == "__main__":

    main()
