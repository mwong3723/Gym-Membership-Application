from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import tables

# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.tables import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User Registration: create an account in the GYM_MEMBER table."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fname = request.form.get("first_name")
        lname = request.form.get("last_name")
        phonenum = request.form.get("phone")

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO GYM_MEMBER (email, password, first_name, last_name, phone_number)
                VALUES (%s, %s, %s, %s, %s)
            ''', (email, hashed_password, fname, lname, phonenum))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("auth.login"))
        except Exception as e:
            return render_template("register.html", error=f"An error occurred: {e}")

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User Login: check credentials in the GYM_MEMBER table."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM GYM_MEMBER WHERE email = %s;", (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and check_password_hash(user[2], password):
                session["user_email"] = email
                return redirect(url_for("dashboard.dashboard"))
            else:
                return render_template("login.html", error="Invalid credentials.")
        except Exception as e:
            return render_template("login.html", error=f"Error accessing database: {e}")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    """Clear the session and redirect to login."""
    session.pop("user_email", None)
    return redirect(url_for("auth.login"))
