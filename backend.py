from flask import Flask, request, jsonify
import sqlite3
from datetime import date, datetime
app = Flask(__name__)

DATABASE = "internflow.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    return "InternFlow Backend is running!"


@app.route("/internships", methods=["POST"])
def add_internship():
    data = request.get_json()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO internships
        (company, role, skills, location, stipend, deadline,
         eligibility, application_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("company"),
        data.get("role"),
        data.get("skills"),
        data.get("location"),
        data.get("stipend"),
        data.get("deadline"),
        data.get("eligibility"),
        data.get("application_link")
    ))

    connection.commit()
    connection.close()

    return jsonify({"message": "Internship added successfully!"}), 201

@app.route("/internships", methods=["GET"])
def get_internships():
    connection = get_db_connection()

    internships = connection.execute(
        "SELECT * FROM internships"
    ).fetchall()

    connection.close()

    return jsonify([dict(internship) for internship in internships])
@app.route("/internships/<int:internship_id>/status", methods=["PUT"])
def update_status(internship_id):
    data = request.get_json()

    new_status = data.get("status")

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        "UPDATE internships SET status = ? WHERE id = ?",
        (new_status, internship_id)
    )

    connection.commit()

    connection.close()

    return jsonify({"message": "Application status updated successfully!"})
@app.route("/internships/deadlines", methods=["GET"])
def upcoming_deadlines():
    connection = get_db_connection()

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
            internship_data = dict(internship)
            internship_data["days_left"] = days_left
            upcoming.append(internship_data)

    return jsonify(upcoming)
if __name__ == "__main__":
    app.run(debug=True)