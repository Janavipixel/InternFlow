import sqlite3
import os
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv("AI/.env")

DATABASE = os.getenv("DATABASE", "internflow.db")


# --------------------------------
# Get all students
# --------------------------------

def get_students():

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    students = connection.execute("""
        SELECT *
        FROM student_preferences
    """).fetchall()

    connection.close()

    return students


# --------------------------------
# Get internships with upcoming deadlines
# --------------------------------

def get_upcoming_deadlines():

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    internships = connection.execute("""
        SELECT *
        FROM internships
        WHERE deadline IS NOT NULL
        AND deadline != ''
    """).fetchall()

    connection.close()

    today = date.today()
    upcoming = []

    for internship in internships:

        try:
            deadline = datetime.strptime(
                internship["deadline"],
                "%Y-%m-%d"
            ).date()

        except ValueError:
            continue

        days_left = (deadline - today).days

        # Only internships whose deadline
        # is today or within the next 7 days
        if 0 <= days_left <= 7:

            upcoming.append({
                "company": internship["company"],
                "role": internship["role"],
                "skills": internship["skills"] or "Not specified",
                "location": internship["location"] or "Not specified",
                "stipend": internship["stipend"] or "Not specified",
                "eligibility": internship["eligibility"] or "Not specified",
                "deadline": internship["deadline"],
                "days_left": days_left,
                "application_link": (
                    internship["application_link"]
                    or "Not available"
                ),
                "match_percentage": internship["match_percentage"]
            })

    return upcoming


# --------------------------------
# Check whether email is due
# --------------------------------

def should_send_email(student):

    frequency = (
        student["email_frequency"] or ""
    ).lower().strip()

    last_email_sent = student["last_email_sent"]

    # First email
    if not last_email_sent:
        return True

    try:
        last_sent_date = datetime.strptime(
            last_email_sent,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return True

    today = date.today()

    days_since_last_email = (
        today - last_sent_date
    ).days

    if frequency == "daily":
        return days_since_last_email >= 1

    if frequency == "weekly":
        return days_since_last_email >= 7

    return False


# --------------------------------
# Update last email date
# --------------------------------

def update_last_email_sent(student_id):

    connection = sqlite3.connect(DATABASE)

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


# --------------------------------
# Send email
# --------------------------------

def send_email(student_email, deadlines):

    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    message = EmailMessage()

    message["Subject"] = (
        "InternFlow - Internship Opportunities"
    )

    message["From"] = sender
    message["To"] = student_email

    body = "Hello!\n\n"

    body += (
        "Here are your upcoming internship "
        "opportunities from InternFlow:\n\n"
    )

    for internship in deadlines:

        body += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        body += (
            f"Company: {internship['company']}\n"
        )

        body += (
            f"Role: {internship['role']}\n"
        )

        body += (
            f"Skills: {internship['skills']}\n"
        )

        body += (
            f"Location: {internship['location']}\n"
        )

        body += (
            f"Stipend: {internship['stipend']}\n"
        )

        body += (
            f"Eligibility: {internship['eligibility']}\n"
        )

        # Match percentage
        match = internship["match_percentage"]

        if match is None:
            match = "Not available"
        else:
            match = f"{match}%"

        body += f"Match: {match}\n"

        body += (
            f"Deadline: {internship['deadline']}\n"
        )

        body += (
            f"Days left: {internship['days_left']}\n"
        )

        body += (
            f"Apply: {internship['application_link']}\n\n"
        )

    body += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    body += (
        "Good luck with your applications!\n\n"
    )

    body += "InternFlow"

    message.set_content(body)

    # Gmail SMTP
    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:

        server.login(
            sender,
            password
        )

        server.send_message(message)

    print(
        f"Email sent successfully to "
        f"{student_email}!"
    )


# --------------------------------
# Main automation
# --------------------------------

if __name__ == "__main__":

    print(
        "Starting InternFlow email automation..."
    )

    students = get_students()

    if not students:

        print(
            "No student preferences found."
        )

        exit()

    print(
        f"Found {len(students)} student(s)."
    )

    deadlines = get_upcoming_deadlines()

    if not deadlines:

        print(
            "No upcoming internship deadlines."
        )

        exit()

    print(
        f"Found {len(deadlines)} "
        "upcoming internships."
    )

    # Send email to each student
    for student in students:

        email = student["email"]

        frequency = (
            student["email_frequency"]
            or "Not specified"
        )

        print(
            f"\nChecking {email} "
            f"(frequency: {frequency})"
        )

        # Check daily / weekly frequency
        if not should_send_email(student):

            print(
                f"Skipping {email} - "
                "email not due yet."
            )

            continue

        try:

            send_email(
                email,
                deadlines
            )

            # Only update the date
            # after successful email
            update_last_email_sent(
                student["id"]
            )

            print(
                f"Last email date updated "
                f"for {email}."
            )

        except Exception as error:

            print(
                f"Failed to send email to "
                f"{email}: {error}"
            )

