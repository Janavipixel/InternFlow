import os
import threading
import concurrent.futures
from datetime import date, datetime, timezone
from dotenv import load_dotenv

# Load environment configuration (.env and AI/.env)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "AI", ".env"))
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from AI.pipeline import search_and_process_internships, deduplicate_skills_list
from AI.matching import calculate_match
from AI.stipend import extract_stipend_amount
from database import create_database, get_db_connection, get_db_matched_internships

# Initialize Flask application
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, allow_private_network=True)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = app.make_default_options_response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Automation-Token, Access-Control-Request-Private-Network"
        res.headers["Access-Control-Allow-Private-Network"] = "true"
        return res

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Automation-Token, Access-Control-Request-Private-Network"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# Ensure database tables exist at startup (vital for Render fresh instances)
create_database()


# =========================================
# STATIC FRONTEND ROUTES
# =========================================

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


@app.route("/script.js")
def serve_script():
    return send_from_directory(".", "script.js")


@app.route("/style.css")
def serve_style():
    return send_from_directory(".", "style.css")


# =========================================
# HEALTH CHECK (FOR RENDER & MONITORING)
# =========================================

@app.route("/health", methods=["GET"])
def health_check():
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception as err:
        print(f"[Health] Database check failed: {err}")

    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "InternFlow API"
    }), status_code


# =========================================
# SAVE AI INTERNSHIP RESULT
# =========================================

def save_internship(internship):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()

        # Check if this internship already exists
        existing = cursor.execute("""
            SELECT id
            FROM internships
            WHERE company = ?
            AND role = ?
            AND location = ?
        """, (
            internship.get("company"),
            internship.get("role"),
            internship.get("location")
        )).fetchone()

        # Don't duplicate existing entries
        if existing:
            return existing["id"]

        skills_val = deduplicate_skills_list(internship.get("skills", []))
        skills_str = ", ".join(skills_val)

        cursor.execute("""
            INSERT INTO internships
            (company, role, skills, location, stipend, deadline,
             eligibility, application_link, match_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            internship.get("company"),
            internship.get("role"),
            skills_str,
            internship.get("location"),
            internship.get("stipend"),
            internship.get("deadline"),
            internship.get("eligibility"),
            internship.get("application_url") or internship.get("application_link"),
            internship.get("match_percentage")
        ))

        internship_id = cursor.lastrowid
        connection.commit()
        return internship_id
    finally:
        connection.close()


# =========================================
# SAVE STUDENT PREFERENCES
# =========================================

@app.route("/save-preferences", methods=["POST"])
def save_preferences():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    email = data.get("email")
    if not email or "@" not in str(email):
        return jsonify({"error": "A valid email address is required"}), 400

    raw_skills = data.get("student_skills", [])
    student_skills = deduplicate_skills_list(raw_skills)
    skills_str = ", ".join(student_skills)

    locations = data.get("locations", [])
    loc_str = ",".join(locations) if isinstance(locations, list) else str(locations or "")

    connection = get_db_connection()
    try:
        cursor = connection.cursor()

        # Check if student is new or has never received an email brief
        existing = cursor.execute(
            "SELECT id, last_email_sent FROM student_preferences WHERE email = ?",
            (email.strip(),)
        ).fetchone()
        is_first_time = (existing is None) or (existing["last_email_sent"] is None)

        cursor.execute("""
            INSERT INTO student_preferences (
                name,
                email,
                student_skills,
                preferred_domain,
                internship_type,
                locations,
                minimum_stipend,
                maximum_duration,
                payment_type,
                work_mode,
                study_year,
                availability,
                deadline_preference,
                company_preference,
                email_frequency
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name = excluded.name,
                student_skills = excluded.student_skills,
                preferred_domain = excluded.preferred_domain,
                internship_type = excluded.internship_type,
                locations = excluded.locations,
                minimum_stipend = excluded.minimum_stipend,
                maximum_duration = excluded.maximum_duration,
                payment_type = excluded.payment_type,
                work_mode = excluded.work_mode,
                study_year = excluded.study_year,
                availability = excluded.availability,
                deadline_preference = excluded.deadline_preference,
                company_preference = excluded.company_preference,
                email_frequency = excluded.email_frequency,
                updated_at = CURRENT_TIMESTAMP
        """, (
            data.get("name"),
            email.strip(),
            skills_str,
            data.get("preferred_domain"),
            data.get("internship_type"),
            loc_str,
            data.get("minimum_stipend"),
            data.get("maximum_duration"),
            data.get("payment_type"),
            data.get("work_mode"),
            data.get("study_year"),
            data.get("availability"),
            data.get("deadline_preference"),
            data.get("company_preference"),
            data.get("email_frequency")
        ))
        connection.commit()

        # Retrieve saved record with allocated student ID
        saved_student = dict(cursor.execute(
            "SELECT * FROM student_preferences WHERE email = ?",
            (email.strip(),)
        ).fetchone())

        # If this is a first-time registration, dispatch welcome brief immediately in background
        if is_first_time:
            def trigger_instant_welcome(student_payload):
                try:
                    from automation import process_student
                    print(f"[Registration] Instant welcome brief initiated for {student_payload.get('email')}...")
                    process_student(student_payload, force=True)
                except Exception as bg_err:
                    print(f"[Registration] Background welcome brief note: {bg_err}")

            threading.Thread(target=trigger_instant_welcome, args=(saved_student,), daemon=True).start()

        return jsonify({
            "message": "Preferences saved successfully!",
            "welcome_email_triggered": is_first_time
        })
    finally:
        connection.close()


@app.route("/preferences", methods=["GET"])
def get_preferences():
    email = request.args.get("email")
    if not email or "@" not in email:
        return jsonify({"error": "A valid email parameter is required"}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        row = cursor.execute(
            "SELECT * FROM student_preferences WHERE email = ?",
            (email.strip(),)
        ).fetchone()

        if not row:
            return jsonify({"found": False, "preferences": None}), 404

        data = dict(row)
        # Parse student_skills and locations into clean lists
        data["student_skills"] = [s.strip() for s in (data.get("student_skills") or "").split(",") if s.strip()]
        data["locations"] = [loc.strip() for loc in (data.get("locations") or "").split(",") if loc.strip()]
        data["has_searched"] = bool(data.get("has_searched", 0))
        return jsonify({"found": True, "preferences": data}), 200
    finally:
        connection.close()





# =========================================
# AI INTERNSHIP SEARCH
# =========================================

@app.route("/search-internships", methods=["POST"])
def search_internships():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    raw_skills = data.get("student_skills", [])
    student_skills = deduplicate_skills_list(raw_skills)
    preferred_domain = (data.get("preferred_domain") or "").strip()
    locations = data.get("locations", [])
    minimum_stipend = data.get("minimum_stipend", 0)
    email = (data.get("email") or "").strip()

    if email:
        try:
            update_conn = get_db_connection()
            update_conn.execute("UPDATE student_preferences SET has_searched = 1 WHERE email = ?", (email,))
            update_conn.commit()
            update_conn.close()
        except Exception as update_err:
            print(f"[API] Error updating has_searched status for {email}: {update_err}")

    if not student_skills:
        return jsonify({"error": "Student skills are required"}), 400

    if not preferred_domain:
        return jsonify({"error": "Preferred domain is required"}), 400

    if not locations:
        return jsonify({"error": "At least one location is required"}), 400

    all_results = []
    seen = set()

    # 1. First load existing verified opportunities from DB (instant baseline)
    try:
        db_results = get_db_matched_internships(
            student_skills,
            preferred_domain,
            locations,
            minimum_stipend
        )
        for it in db_results:
            key = (
                str(it.get("company", "")).strip().lower(),
                str(it.get("role", "")).strip().lower(),
                str(it.get("location", "")).strip().lower()
            )
            if key not in seen:
                seen.add(key)
                all_results.append(it)
    except Exception as db_err:
        print(f"[API] Error loading database opportunities: {db_err}")

    # 2. If fewer than 4 verified opportunities found in DB, run live discovery for top location
    if len(all_results) < 4:
        search_locations = [l for l in locations if l.lower() != "anywhere in india"][:1]
        if not search_locations:
            search_locations = ["Remote"]

        try:
            for loc in search_locations:
                live_results = search_and_process_internships(
                    student_skills,
                    preferred_domain,
                    loc,
                    minimum_stipend
                )
                if live_results:
                    for internship in live_results:
                        key = (
                            str(internship.get("company", "")).strip().lower(),
                            str(internship.get("role", "")).strip().lower(),
                            str(internship.get("location", "")).strip().lower()
                        )
                        if key not in seen:
                            seen.add(key)
                            internship_id = save_internship(internship)
                            internship["id"] = internship_id
                            all_results.append(internship)
        except Exception as search_err:
            print(f"[API] Live search runner note: {search_err}")

    # Sort opportunities by match percentage descending, prioritizing opportunities with deadlines
    all_results.sort(
        key=lambda x: (
            float(x.get("match_percentage") or 0),
            1 if x.get("deadline") else 0
        ),
        reverse=True
    )

    return jsonify({
        "count": len(all_results),
        "internships": all_results
    })


# =========================================
# MANUAL INTERNSHIP MANAGEMENT
# =========================================

@app.route("/internships", methods=["POST"])
def add_internship():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    connection = get_db_connection()
    try:
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
        return jsonify({"message": "Internship added successfully!"}), 201
    finally:
        connection.close()


@app.route("/internships", methods=["GET"])
def get_internships():
    connection = get_db_connection()
    try:
        internships = connection.execute("SELECT * FROM internships ORDER BY id DESC").fetchall()
        return jsonify([dict(item) for item in internships])
    finally:
        connection.close()


@app.route("/saved-internships", methods=["GET"])
def get_saved_internships():
    connection = get_db_connection()
    try:
        internships = connection.execute(
            "SELECT * FROM internships WHERE saved = 1 ORDER BY id DESC"
        ).fetchall()
        return jsonify([dict(item) for item in internships])
    finally:
        connection.close()


@app.route("/internships/<int:internship_id>/status", methods=["PUT"])
def update_status(internship_id):
    data = request.get_json() or {}
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE internships SET status = ? WHERE id = ?",
            (new_status, internship_id)
        )
        connection.commit()
        return jsonify({"message": "Application status updated successfully!"})
    finally:
        connection.close()


@app.route("/internships/<int:internship_id>/save", methods=["PUT"])
def save_internship_for_student(internship_id):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE internships SET saved = 1 WHERE id = ?",
            (internship_id,)
        )
        connection.commit()
        return jsonify({"message": "Internship saved successfully!"})
    finally:
        connection.close()


@app.route("/internships/deadlines", methods=["GET"])
def upcoming_deadlines():
    connection = get_db_connection()
    try:
        internships = connection.execute("SELECT * FROM internships").fetchall()
        today = date.today()
        upcoming = []

        for item in internships:
            deadline_str = item["deadline"]
            if not deadline_str:
                continue

            try:
                deadline_dt = datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue

            days_left = (deadline_dt - today).days
            if 0 <= days_left <= 7:
                row_dict = dict(item)
                row_dict["days_left"] = days_left
                upcoming.append(row_dict)

        return jsonify(upcoming)
    finally:
        connection.close()


# =========================================
# AUTOMATION COORDINATION ENDPOINTS
# =========================================

@app.route("/automation/students", methods=["GET"])
def automation_students():
    token = request.headers.get("X-Automation-Token")
    expected_token = os.getenv("AUTOMATION_TOKEN")

    if not expected_token or not token or token.strip() != expected_token.strip():
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    try:
        students = connection.execute("SELECT * FROM student_preferences").fetchall()
        return jsonify([dict(student) for student in students])
    finally:
        connection.close()


@app.route("/automation/email-sent/<int:student_id>", methods=["PUT"])
def automation_email_sent(student_id):
    token = request.headers.get("X-Automation-Token")
    expected_token = os.getenv("AUTOMATION_TOKEN")

    if not expected_token or not token or token.strip() != expected_token.strip():
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    try:
        connection.execute("""
            UPDATE student_preferences
            SET last_email_sent = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (date.today().isoformat(), student_id))
        connection.commit()
        return jsonify({"message": "Email date updated successfully"})
    finally:
        connection.close()


@app.route("/student/email-status", methods=["GET"])
def student_email_status():
    email = request.args.get("email")
    if not email or "@" not in email:
        return jsonify({"error": "A valid email parameter is required"}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        student = cursor.execute(
            "SELECT id, name, email, email_frequency, last_email_sent, updated_at FROM student_preferences WHERE email = ?",
            (email.strip(),)
        ).fetchone()

        if not student:
            return jsonify({"error": "Student preferences not found"}), 404

        student_dict = dict(student)

        # Retrieve recent email logs for this student
        logs = cursor.execute("""
            SELECT timestamp_utc, eligible_internships_count, status, provider_status_code, error_category
            FROM email_logs
            WHERE student_id = ?
            ORDER BY id DESC LIMIT 5
        """, (student_dict["id"],)).fetchall()

        logs_list = [dict(log) for log in logs]

        return jsonify({
            "email": student_dict["email"],
            "email_frequency": student_dict.get("email_frequency") or "Daily",
            "last_email_sent": student_dict.get("last_email_sent"),
            "recent_logs": logs_list
        })
    finally:
        connection.close()


@app.route("/automation/trigger-test", methods=["POST"])
def trigger_test_email():
    data = request.get_json() or {}
    email = data.get("email")

    if not email or "@" not in email:
        return jsonify({"error": "A valid email is required"}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        student_row = cursor.execute(
            "SELECT * FROM student_preferences WHERE email = ?",
            (email.strip(),)
        ).fetchone()

        if not student_row:
            return jsonify({"error": "Student preferences not found. Please save preferences first."}), 404

        student = dict(student_row)
    finally:
        connection.close()

    try:
        from automation import process_student
        outcome = process_student(student, force=True)

        if outcome == "accepted_by_provider":
            return jsonify({
                "success": True,
                "status": "accepted_by_provider",
                "message": f"Personalized brief successfully sent to {email}! Please check your inbox."
            })
        elif outcome == "skipped_no_matching_internships":
            return jsonify({
                "success": False,
                "status": "skipped_no_matching_internships",
                "message": "No active internships currently match your criteria and deadlines."
            })
        elif outcome == "skipped_incomplete_preferences":
            return jsonify({
                "success": False,
                "status": "skipped_incomplete_preferences",
                "message": "Preferences are incomplete. Please specify skills, preferred domain, and location."
            })
        elif outcome == "cloud_smtp_blocked":
            return jsonify({
                "success": False,
                "status": "cloud_smtp_blocked",
                "message": "Render's Free Tier blocks outgoing SMTP ports (465 & 587) to prevent spam. Emails are designed to be sent automatically via the scheduled GitHub Actions runner in your repo or when running locally on your computer at http://127.0.0.1:5000. (To send directly from Render, you can also add a free RESEND_API_KEY)."
            }), 200
        else:
            reason = "EMAIL_ADDRESS or EMAIL_PASSWORD not configured"
            provider_code = ""
            try:
                conn = get_db_connection()
                last_log = conn.execute(
                    "SELECT provider_status_code, error_category FROM email_logs WHERE recipient_email_masked LIKE ? OR student_id = ? ORDER BY id DESC LIMIT 1",
                    (f"%{email[-10:]}", student.get("id"))
                ).fetchone()
                conn.close()
                if last_log:
                    provider_code = last_log["provider_status_code"] or ""
                    if last_log["error_category"]:
                        reason = last_log["error_category"]
                    elif last_log["provider_status_code"]:
                        reason = f"SMTP Code {last_log['provider_status_code']}"
            except Exception:
                pass

            if (
                provider_code == "CLOUD_SMTP_BLOCKED"
                or "Render Free Tier blocks" in reason
                or "network is unreachable" in reason.lower()
                or "invalid argument" in reason.lower()
                or "errno 22" in reason.lower()
            ):
                return jsonify({
                    "success": False,
                    "status": "cloud_smtp_blocked",
                    "message": "Render's Free Tier blocks outgoing SMTP ports (465 & 587) to prevent spam. Emails are designed to be sent automatically via the scheduled GitHub Actions runner in your repo or when running locally on your computer at http://127.0.0.1:5000. (To send directly from Render, you can also add a free RESEND_API_KEY)."
                }), 200

            return jsonify({
                "success": False,
                "status": outcome,
                "message": f"Email delivery failed: {reason}. Please ensure EMAIL_ADDRESS and EMAIL_PASSWORD (Gmail App Password) are added to your Render Environment Variables."
            }), 500
    except Exception as err:
        err_str = str(err)
        print(f"[Automation] Unhandled trigger-test error: {err_str}")
        if (
            "errno 22" in err_str.lower()
            or "invalid argument" in err_str.lower()
            or "network is unreachable" in err_str.lower()
            or "connection refused" in err_str.lower()
        ):
            return jsonify({
                "success": False,
                "status": "cloud_smtp_blocked",
                "message": "Render's Free Tier blocks outgoing SMTP ports (465 & 587) to prevent spam. Emails are designed to be sent automatically via the scheduled GitHub Actions runner in your repo or when running locally on your computer at http://127.0.0.1:5000. (To send directly from Render, you can also add a free RESEND_API_KEY)."
            }), 200
        return jsonify({
            "success": False,
            "error": f"Internal automation error: {err_str}"
        }), 500


# =========================================
# SERVER STARTUP
# =========================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1")
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
