from flask import Flask, flash, render_template, request, redirect, url_for, session
import psycopg2 as psy
from werkzeug.security import check_password_hash, generate_password_hash
from models import tables
from models import get_db_connection
from datetime import date
from dateutil.relativedelta import relativedelta


# Database Connection Info
hostname = 'dpg-cvoqt3adbo4c73b7ot6g-a.oregon-postgres.render.com'
database = 'dbname_uvr7'
username = 'dbname'
pwd = 'u4TY7DucVnYJPmFjAKSgnJZsRoLCoDia'
port_id = 5432

tables.initTables(hostname, database, username, pwd, port_id)

app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"  # Replace with a secure key in production

FITNESS_CLASSES = [
    {"id": 1, "name": "Yoga Class", "day": "Monday", "time": "8:00 AM"},
    {"id": 2, "name": "Spin Class", "day": "Wednesday", "time": "6:00 PM"},
    {"id": 3, "name": "HIIT Class", "day": "Friday", "time": "7:00 AM"},
]

WORKOUT_LOGS = []  # We'll store workouts in memory for now

@app.route("/trainers")
def trainer_list():
    if "user_email" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM Trainer;')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Convert each row to a dict
        trainers = []
        for row in rows:
            trainers.append({
                "trainer_id": row[0],
                "name": row[1],
                "expertise": row[2],
                "contact_info": row[3],
                "bio": row[4]
            })

        return render_template("trainers.html", trainers=trainers)
    except Exception as e:
        return f"Error fetching trainers: {e}"

@app.route("/trainer/<int:trainer_id>")
def trainer_detail(trainer_id):
    """
    Displays a single trainer's info from the TRAINER table.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM trainer WHERE trainer_id = %s;", (trainer_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return "Trainer not found", 404

        trainer = {
            "trainer_id": row[0],
            "name": row[1],
            "expertise": row[2],
            "contact_info": row[3],
            "bio": row[4]
        }
        return render_template("trainer_detail.html", trainer=trainer)
    except Exception as e:
        return f"Error fetching trainer detail: {e}"


# Home / Register / Login / Logout
@app.route("/")
def home():
    """ Redirect to login if not logged in; else go to dashboard. """
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    if "admin_email" in session:
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        phonenum = request.form.get("phone")

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO Member (name, email, password, phone)
                VALUES (%s, %s, %s, %s)
            ''', (name, email, hashed_password, phonenum))
            conn.commit()
            cur.close()
            conn.close()

            return redirect(url_for("login"))
        except psy.IntegrityError:
            # Email already registered
            return render_template("register.html", error="Email is already registered.")
        except Exception as e:
            return render_template("register.html", error=f"An error occurred: {e}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM Member WHERE email = %s;", (email,))
            user = cur.fetchone()
            cur.execute("SELECT * FROM Admin WHERE email = %s;", (email,))
            admin = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                stored_hashed_pw = user[3]
                if check_password_hash(stored_hashed_pw, password):
                    session["user_email"] = email
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("login.html", error="Invalid password.")
            elif admin:
                if admin[3] == password:
                    session["admin_email"] = email
                    return redirect(url_for("admin_dashboard"))
                else:
                    return render_template("login.html", error="Invalid password.")
            else:
                return render_template("login.html", error="Email not found.")
        except Exception as e:
            return render_template("login.html", error=f"Error accessing database: {e}")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """ Clear the session, then redirect to login. """
    session.pop("user_email", None)
    session.pop("admin_email", None)
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_email" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Member WHERE email=%s",(session.get('user_email'),))
    member = cur.fetchone()
    cur.close()
    conn.close()

    message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")
        update = request.form.get("update")

        if form_type == "membership":
            selected_plan_id = request.form.get("plan_id")

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM MembershipPlan where plan_id=%s",(selected_plan_id,))
            plan = cur.fetchone()
            cur.close()
            conn.close()

            current_date = date.today()
            end_date = current_date + relativedelta(months=(plan[2])) 

            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''
                            INSERT INTO Membership (member_id, plan_id, start_date, end_date, status) 
                            VALUES (%s, %s, %s, %s, %s)''', (member[0],plan[0],current_date,end_date,"active",))
                conn.commit()
                cur.close()
                conn.close() 
            except Exception as e:
                message = f"Membership already registered"


        elif form_type == "book_class":
            class_id = request.form.get("class_id")
            message = f"You booked class ID = {class_id} (Mock)"

        elif form_type == "log_workout":
            workout_details = request.form.get("workout_details")
            WORKOUT_LOGS.append(workout_details)
            message = "Workout logged successfully! (Mock)"
        
        if update == "renew":
            target_membership = request.form.get("plan_id")

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM MembershipPlan where plan_id=%s",(target_membership,))
            plan = cur.fetchone()
            cur.close()
            conn.close()

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM Membership where plan_id=%s",(target_membership,))
            membership = cur.fetchone()
            cur.close()
            conn.close()

            end_date = membership[3] + relativedelta(months=(plan[2])) 

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE Membership SET status=%s, end_date=%s where plan_id=%s",
                        ("renewed",end_date,target_membership,))
            conn.commit()
            cur.close()
            conn.close()

        elif update == "cancel":
            target_membership = request.form.get("plan_id")
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE Membership SET status=%s where plan_id=%s",
                        ("canceled",target_membership,))
            conn.commit()
            cur.close()
            conn.close()

    plans = []
    memberships = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM MembershipPlan")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            plans.append({
                "id": row[0],
                "name": row[1],
                "length": row[2],
                "price": row[3]
            })

    except Exception as e:
        message = f"Error fetching membership plans: {e}"

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Membership WHERE member_id=%s", (member[0],))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            memberships.append({
                "plan_id": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "status": row[4],
            })

    except Exception as e:
        message = f"Error fetching membership plans: {e}"

    return render_template(
            "dashboard.html",
            membership_plans=plans,
            membership=memberships,
            fitness_classes=FITNESS_CLASSES,
            workout_logs=WORKOUT_LOGS,
            message=message
        )

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    plans = []
    trainers = []
    message = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM MembershipPlan")
        planData = cur.fetchall()
        cur.execute("SELECT * FROM Trainer")
        trainerData = cur.fetchall()
        cur.close()
        conn.close()

        for row in planData:
            plans.append({
                "id": row[0],
                "name": row[1],
                "length": row[2],
                "price": row[3]
            })
        
        for row in trainerData:
            trainers.append({
                "id": row[0],
                "name": row[1],
                "expertise": row[2],
                "contact_info": row[3],
                "description": row[4]
            })
        
    except Exception as e:
        message=f"Error accessing database: {e}"
    
    if request.method == "POST":
        operation = request.form.get("trainer")

        if operation == "insert":
            name = request.form.get("name")
            expertise = request.form.get("expertise")
            contact = request.form.get("contact_info")
            desc = request.form.get("description")

            if not name:
                flash("Trainer name cannot be left empty", "error")
                return redirect(url_for('admin_dashboard'))
            
            if not contact:
                flash("Trainer must have contact information", "error")
                return redirect(url_for('admin_dashboard'))
            
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''
                        INSERT INTO Trainer (name, expertise, contact_info, description)
                        VALUES (%s, %s, %s, %s)
                    ''', (name, expertise, contact, desc,))
                conn.commit()
                cur.close()
                conn.close()
            
            except Exception as e:
                print(f"Error with database: {e}")

            return redirect(url_for('admin_dashboard'))
        
        elif operation == "update":
            id = request.form.get("id")
            name = request.form.get("name")
            expertise = request.form.get("expertise")
            contact = request.form.get("contact_info")
            desc = request.form.get("description")

            if not name:
                flash("Trainer name cannot be left empty", "error")
                return redirect(url_for('admin_dashboard'))
            
            if not contact:
                flash("Trainer must have contact information", "error")
                return redirect(url_for('admin_dashboard'))

            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                '''UPDATE Trainer SET name=%s, expertise=%s, contact_info=%s, description=%s where trainer_id=%s''', 
                (name, expertise, contact, desc, id,))
                conn.commit()
                cur.close()
                conn.close()
            
            except Exception as e:
                print(f"Error with database: {e}")

            return redirect(url_for('admin_dashboard'))
        
        elif operation == "delete":
            id = request.form.get("id")
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('''DELETE FROM Trainer where trainer_id = %s''', (id,))
                conn.commit()
                cur.close()
                conn.close()

            except Exception as e:
                print(f"Error with database: {e}")
            
            return redirect(url_for('admin_dashboard'))


    return render_template("admin_dashboard.html", plans=plans, trainers=trainers, error=message)


# @app.route("/admin_dashboard/generate_report", methods=["POST"])
# def generate_trainer_report():
#     print("✅ Route is working")
#     return "<h1>Trainer Report Reached!</h1>"

@app.route("/admin_dashboard/generate_report", methods=["POST"])
def generate_trainer_report():
    print("==== Trainer Report Route Triggered ====")

    trainer_id = request.form.get("trainer_id")

    if not trainer_id:
        flash("No trainer selected for report.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get trainer name
        cur.execute("SELECT name FROM Trainer WHERE trainer_id = %s", (trainer_id,))
        trainer_row = cur.fetchone()
        if not trainer_row:
            flash("Trainer not found.", "error")
            return redirect(url_for("admin_dashboard"))

        trainer_name = trainer_row[0]

        # Get workouts
        cur.execute("""
            SELECT workout_date, description 
            FROM WorkoutLog 
            WHERE trainer_id = %s 
            ORDER BY workout_date DESC;
        """, (trainer_id,))
        workout_rows = cur.fetchall()

        cur.close()
        conn.close()

        workouts = [{"date": row[0], "description": row[1]} for row in workout_rows]

        report = {
            "trainer_name": trainer_name,
            "total_workouts": len(workouts),
            "workouts": workouts
        }

        return render_template("trainer_report.html", report=report)

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Error generating report: {e}", "error")
        return redirect(url_for("admin_dashboard"))


if __name__ == "__main__": 
    app.run(debug=True)