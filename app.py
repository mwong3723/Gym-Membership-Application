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
# ---------------------------------------------------------------------
# Dashboard  – now loads FitnessClass from the DB
# ---------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    # ---------- access control ----------
    if "user_email" not in session:
        return redirect(url_for("login"))

    # ---------- load current member ----------
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM Member WHERE email=%s;",
                (session.get("user_email"),))
    member = cur.fetchone()
    cur.close(); conn.close()

    message = None

    # =================================================================
    # POST HANDLING  (unchanged from your original code)
    # =================================================================
    if request.method == "POST":
        form_type = request.form.get("form_type")
        update    = request.form.get("update")

        # ----- buy a membership plan -----
        if form_type == "membership":
            selected_plan_id = request.form.get("plan_id")

            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT * FROM MembershipPlan WHERE plan_id=%s;",
                        (selected_plan_id,))
            plan = cur.fetchone()
            cur.close(); conn.close()

            current_date = date.today()
            end_date     = current_date + relativedelta(months=plan[2])

            try:
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO Membership (member_id, plan_id,
                                            start_date, end_date, status)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (member[0], plan[0], current_date, end_date, "active")
                )
                conn.commit()
            except Exception:
                message = "Membership already registered"
            finally:
                cur.close(); conn.close()

        # ----- book a class  (still mock) -----
        elif form_type == "book_class":
            class_id = request.form.get("class_id")
            message  = f"You booked class ID = {class_id} (Mock)"

        # ----- log workout (mock) -----
        elif form_type == "log_workout":
            WORKOUT_LOGS.append(request.form.get("workout_details"))
            message = "Workout logged successfully! (Mock)"

        # ----- renew / cancel -----
        if update == "renew":
            target_plan = request.form.get("plan_id")

            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT * FROM MembershipPlan WHERE plan_id=%s;",
                        (target_plan,)); plan = cur.fetchone()
            cur.execute("SELECT * FROM Membership WHERE plan_id=%s;",
                        (target_plan,)); membership = cur.fetchone()
            cur.close(); conn.close()

            new_end = membership[3] + relativedelta(months=plan[2])

            conn = get_db_connection(); cur = conn.cursor()
            cur.execute(
                "UPDATE Membership SET status=%s, end_date=%s WHERE plan_id=%s;",
                ("renewed", new_end, target_plan)
            )
            conn.commit(); cur.close(); conn.close()

        elif update == "cancel":
            target_plan = request.form.get("plan_id")
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute(
                "UPDATE Membership SET status=%s WHERE plan_id=%s;",
                ("canceled", target_plan)
            )
            conn.commit(); cur.close(); conn.close()

    # =================================================================
    # DATA LOAD  – plans, memberships, trainers (unchanged)
    # =================================================================
    plans = []
    memberships = []

    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM MembershipPlan"); rows = cur.fetchall()
        for r in rows:
            plans.append({"id": r[0], "name": r[1],
                          "length": r[2], "price": r[3]})
    finally:
        cur.close(); conn.close()

    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM Membership WHERE member_id=%s;",
                    (member[0],))
        rows = cur.fetchall()
        for r in rows:
            memberships.append({"plan_id": r[1], "start_date": r[2],
                                "end_date": r[3], "status": r[4]})
    finally:
        cur.close(); conn.close()

    trainers = []
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            "SELECT trainer_id, name, expertise, contact_info FROM Trainer;"
        )
        for r in cur.fetchall():
            trainers.append({"trainer_id": r[0], "name": r[1],
                             "expertise": r[2], "contact_info": r[3]})
    finally:
        cur.close(); conn.close()

    # =================================================================
    # NEW  – load fitness classes from DB (fallback to static list)
    # =================================================================
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            """
            SELECT class_id, class_name, description,
                   schedule, capacity, trainer_id
              FROM FitnessClass
             ORDER BY class_id;
            """
        )
        class_rows = cur.fetchall()
        fitness_classes = [
            {"id": r[0], "name": r[1], "description": r[2],
             "schedule": r[3], "capacity": r[4], "trainer_id": r[5]}
            for r in class_rows
        ]
        if not fitness_classes:            # table empty
            fitness_classes = FITNESS_CLASSES
    except Exception as e:
        message = f"Error loading classes: {e}"
        fitness_classes = FITNESS_CLASSES
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

    # =================================================================
    # RENDER
    # =================================================================
    return render_template(
        "dashboard.html",
        membership_plans = plans,
        membership       = memberships,
        fitness_classes  = fitness_classes,
        workout_logs     = WORKOUT_LOGS,
        trainers         = trainers,
        message          = message
    )


# ---------------------------------------------------------------------
# Admin Dashboard + its helper routes
# ---------------------------------------------------------------------

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    plans, trainers, classes = [], [], []
    message = None

    # ===============================================================
    # POST  ── handle Trainer or FitnessClass actions
    # ===============================================================
    if request.method == "POST":
        form_type = request.form.get("form_type")      # "trainer" | "class"

        # ------------------ FITNESS CLASS CRUD ---------------------
        if form_type == "class":
            action      = request.form.get("action")   # insert / update / delete
            class_id    = request.form.get("class_id")
            class_name  = request.form.get("class_name")
            description = request.form.get("description")
            schedule    = request.form.get("schedule")
            capacity    = request.form.get("capacity")
            trainer_id  = request.form.get("trainer_id")

            try:
                conn = get_db_connection(); cur = conn.cursor()

                if action == "insert":
                    cur.execute(
                        """
                        INSERT INTO FitnessClass
                            (class_name, description, schedule,
                             capacity, trainer_id)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (class_name, description, schedule, capacity, trainer_id)
                    )
                elif action == "update":
                    cur.execute(
                        """
                        UPDATE FitnessClass
                           SET class_name=%s, description=%s, schedule=%s,
                               capacity=%s, trainer_id=%s
                         WHERE class_id=%s;
                        """,
                        (class_name, description, schedule,
                         capacity, trainer_id, class_id)
                    )
                elif action == "delete":
                    cur.execute("DELETE FROM FitnessClass WHERE class_id=%s;",
                                (class_id,))
                conn.commit(); flash("Class operation successful", "success")
            except Exception as e:
                conn.rollback(); flash(f"Class DB error: {e}", "error")
            finally:
                cur.close(); conn.close()
            return redirect(url_for("admin_dashboard"))

        # ------------------ TRAINER CRUD (original) ---------------
        elif form_type == "trainer":
            operation = request.form.get("action")      # insert / update / delete
            tid       = request.form.get("trainer_id")
            name      = request.form.get("name")
            expertise = request.form.get("expertise")
            contact   = request.form.get("contact_info")
            desc      = request.form.get("description")

            try:
                conn = get_db_connection(); cur = conn.cursor()
                if operation == "insert":
                    cur.execute(
                        """
                        INSERT INTO Trainer (name, expertise, contact_info, description)
                        VALUES (%s,%s,%s,%s);
                        """, (name, expertise, contact, desc)
                    )
                elif operation == "update":
                    cur.execute(
                        """
                        UPDATE Trainer
                           SET name=%s, expertise=%s, contact_info=%s, description=%s
                         WHERE trainer_id=%s;
                        """, (name, expertise, contact, desc, tid)
                    )
                elif operation == "delete":
                    cur.execute("DELETE FROM Trainer WHERE trainer_id=%s;", (tid,))
                conn.commit(); flash("Trainer operation successful", "success")
            except Exception as e:
                conn.rollback(); flash(f"Trainer DB error: {e}", "error")
            finally:
                cur.close(); conn.close()
            return redirect(url_for("admin_dashboard"))

    # ===============================================================
    # GET  ── load Plans, Trainers, Classes for display
    # ===============================================================
    try:
        conn = get_db_connection(); cur = conn.cursor()

        cur.execute("SELECT * FROM MembershipPlan ORDER BY plan_id;")
        planData = cur.fetchall()

        cur.execute("SELECT * FROM Trainer ORDER BY trainer_id;")
        trainerData = cur.fetchall()

        cur.execute("SELECT * FROM FitnessClass ORDER BY class_id;")
        classData = cur.fetchall()

        cur.close(); conn.close()

        for p in planData:
            plans.append({"id": p[0], "name": p[1], "length": p[2], "price": p[3]})

        for t in trainerData:
            trainers.append({
                "id": t[0], "name": t[1], "expertise": t[2],
                "contact_info": t[3], "description": t[4]
            })

        for c in classData:
            classes.append({
                "id": c[0], "name": c[1], "description": c[2],
                "schedule": c[3], "capacity": c[4], "trainer_id": c[5]
            })

    except Exception as e:
        message = f"Error accessing database: {e}"

    return render_template(
        "admin_dashboard.html",
        plans    = plans,
        trainers = trainers,
        classes  = classes,   # NEW
        error    = message
    )

# ------------------------------------------------------------------
#  Membership-Plan helper routes  (unchanged)
# ------------------------------------------------------------------
@app.route("/admin_dashboard/create", methods=["POST"])
def createPlan():
    name   = request.form['name']
    length = request.form['length']
    price  = request.form['price']
    if not name or not length.isdigit() or not price:
        flash("Invalid plan data", "error")
        return redirect(url_for('admin_dashboard'))
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO MembershipPlan (plan_name, duration, price) VALUES (%s, %s, %s);",
            (name, length, price)
        ); conn.commit()
    finally:
        cur.close(); conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard/update", methods=["POST"])
def updatePlan():
    pid    = request.form['id']
    name   = request.form['name']
    length = request.form['length']
    price  = request.form['price']
    if not name or not length.isdigit() or not price:
        flash("Invalid plan data", "error")
        return redirect(url_for('admin_dashboard'))
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            "UPDATE MembershipPlan SET plan_name=%s, duration=%s, price=%s WHERE plan_id=%s;",
            (name, length, price, pid)
        ); conn.commit()
    finally:
        cur.close(); conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard/delete", methods=["POST"])
def deletePlan():
    pid = request.form['id']
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM MembershipPlan WHERE plan_id=%s;", (pid,))
        conn.commit()
    finally:
        cur.close(); conn.close()
    return redirect(url_for('admin_dashboard'))

# ------------------------------------------------------------------
#  Trainer report route  (unchanged)
# ------------------------------------------------------------------
@app.route("/admin_dashboard/generate_report", methods=["POST"])
def generate_trainer_report():
    trainer_id = request.form.get("trainer_id")
    if not trainer_id:
        flash("No trainer selected for report.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            """
            SELECT trainer_id, name, expertise, contact_info, description
              FROM Trainer
             WHERE trainer_id=%s;
            """, (trainer_id,)
        ); row = cur.fetchone()
        cur.close(); conn.close()

        if not row:
            flash("Trainer not found.", "error")
            return redirect(url_for("admin_dashboard"))

        trainer = {
            "id": row[0], "name": row[1], "expertise": row[2],
            "contact_info": row[3], "description": row[4]
        }
        return render_template("trainer_report.html", trainer=trainer)

    except Exception as e:
        flash(f"Error generating report: {e}", "error")
        return redirect(url_for("admin_dashboard"))

@app.route("/view_classes")
def view_classes():
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("classes.html", fitness_classes=FITNESS_CLASSES)


if __name__ == "__main__": 
    app.run(debug=True)
