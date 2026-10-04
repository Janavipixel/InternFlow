import sqlite3
import os
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


DATABASE = os.getenv("DATABASE", "internflow.db")


def get_upcoming_deadlines():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    internships = connection.execute(
        "SELECT * FROM internships"
    ).fetchall()

    connection.close()

    today = date.today()
    upcoming = []

    for internship in internships:
        deadline = datetime.strptime(
            internship["deadline"], "%Y-%m-%d"
        ).date()

        days_left = (deadline - today).days

        if 0 <= days_left <= 7:
            upcoming.append({
                "company": internship["company"],
                "role": internship["role"],
                "deadline": internship["deadline"],
                "days_left": days_left,
                "application_link": internship["application_link"]
            })

    return upcoming
def send_email(subject, body):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = sender
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(message)

    print("Email sent successfully!")


if __name__ == "__main__":
    deadlines = get_upcoming_deadlines()

    if deadlines:
        print("Upcoming internship deadlines:")

        for internship in deadlines:
            print(
                f"{internship['company']} - "
                f"{internship['role']} - "
                f"{internship['days_left']} days left"
            )

        body = "InternFlow Deadline Reminder\n\n"

        for internship in deadlines:
            body += (
                f"Company: {internship['company']}\n"
                f"Role: {internship['role']}\n"
                f"Deadline: {internship['deadline']}\n"
                f"Days left: {internship['days_left']}\n"
                f"Apply here: {internship['application_link']}\n\n"
            )

        send_email(
            "InternFlow - Internship Deadline Reminder",
            body
        )

    else:
        print("No upcoming internship deadlines.")