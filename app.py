from flask import Flask, flash, render_template, request, redirect, url_for, session
import psycopg2 as psy
from werkzeug.security import check_password_hash, generate_password_hash
from models import tables
from datetime import date
from dateutil.relativedelta import relativedelta

# ---------------------------------------------------------------------
# Database Connection Info
# ---------------------------------------------------------------------
hostname = 'dpg-cvoqt3adbo4c73b7ot6g-a.oregon-postgres.render.com'
database = 'dbname_uvr7'
username = 'dbname'
pwd      = 'u4TY7DucVnYJPmFjAKSgnJZsRoLCoDia'
port_id  = 5432

# ---------------------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"

# ---------------------------------------------------------------------
# Initialize tables & DB helper
# ---------------------------------------------------------------------
tables.initTables(hostname, database, username, pwd, port_id)

def get_db_connection():
    return psy.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id
    )

# In-memory workout logs
WORKOUT_LOGS = []

# ---------------------------------------------------------------------
# Trainer CRUD
# ---------------------------------------------------------------------
@app.route("/add_trainer", methods=["GET", "POST"])
def add_trainer():
    if request.method == "POST":
        name         = request.form['name']
        expertise    = request.form['expertise']
        contact_info = request.form['contact_info']
        bio          = request.form['contact_info']
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO TRAINER (name, expertise, contact_info, bio) VALUES (%s, %s, %s, %s);",
                (name, expertise, contact_info, bio)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("trainer_list"))
    return render_template("add_trainer.html")

@app.route("/trainers")
def trainer_list():
    if "user_email" not in session:
        return redirect(url_for("login"))
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute('SELECT trainer_id, name, expertise, contact_info, description FROM "TRAINER";')
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    trainers = [
        {"trainer_id": r[0], "name": r[1], "expertise": r[2], "contact_info": r[3], "description": r[4]}
        for r in rows
    ]
    return render_template("trainers.html", trainers=trainers)

@app.route("/trainer/<int:trainer_id>")
def trainer_detail(trainer_id):
    if "user_email" not in session:
        return redirect(url_for("login"))
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT trainer_id, name, expertise, contact_info, description FROM TRAINER WHERE trainer_id = %s;",
            (trainer_id,)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    if not row:
        return "Trainer not found", 404
    trainer = {
        "trainer_id":  row[0],
        "name":         row[1],
        "expertise":    row[2],
        "contact_info": row[3],
        "description":          row[4]
    }
    return render_template("trainer_detail.html", trainer=trainer)

# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------
@app.route("/")
def home():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    if "admin_email" in session:
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email     = request.form['email']
        password  = request.form['password']
        name      = request.form['name']
        phone     = request.form['phone']
        hashed_pw = generate_password_hash(password)
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO Member (name, email, password, phone) VALUES (%s, %s, %s, %s);",
                (name, email, hashed_pw, phone)
            )
            conn.commit()
        except psy.IntegrityError:
            return render_template("register.html", error="Email is already registered.")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form['email']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("SELECT * FROM Member WHERE email = %s;", (email,))
            user  = cur.fetchone()
            cur.execute("SELECT * FROM Admin WHERE email = %s;", (email,))
            admin = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if user:
            if check_password_hash(user[3], password):
                session['user_email'] = email
                return redirect(url_for('dashboard'))
            else:
                return render_template("login.html", error="Invalid password.")
        if admin:
            if admin[3] == password:
                session['admin_email'] = email
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template("login.html", error="Invalid password.")
        return render_template("login.html", error="Email not found.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_email', None)
    session.pop('admin_email', None)
    return redirect(url_for('login'))

# ---------------------------------------------------------------------
# User Dashboard
# ---------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    # load member
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM Member WHERE email=%s;", (session['user_email'],))
    member = cur.fetchone()
    cur.close()
    conn.close()

    message = None
    if request.method == "POST":
        # existing POST logic...
        pass

    # membership plans
    plans = []
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT plan_id, plan_name, duration, price FROM MembershipPlan;")
    for r in cur.fetchall():
        plans.append({"id": r[0], "name": r[1], "length": r[2], "price": r[3]})
    cur.close()
    conn.close()

    # member's memberships
    memberships = []
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT plan_id, start_date, end_date, status FROM Membership WHERE member_id=%s;", (member[0],))
    for r in cur.fetchall():
        memberships.append({"plan_id": r[0], "start_date": r[1], "end_date": r[2], "status": r[3]})
    cur.close()
    conn.close()

    # trainers
    trainers = []
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT trainer_id, name, expertise, contact_info FROM Trainer;")
    for r in cur.fetchall():
        trainers.append({"trainer_id": r[0], "name": r[1], "expertise": r[2], "contact_info": r[3]})
    cur.close()
    conn.close()

    # fitness classes
    fitness_classes = []
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT class_id, class_name, description, schedule, capacity, trainer_id
              FROM FitnessClass
             ORDER BY class_id;
            """
        )
        rows = cur.fetchall()
        fitness_classes = [
            {
                'class_id':    r[0],
                'class_name':  r[1],
                'description': r[2],
                'schedule':    r[3],
                'capacity':    r[4],
                'trainer_id':  r[5]
            }
            for r in rows
        ]
    except Exception as e:
        message = f"Error loading classes: {e}"
    finally:
        cur.close()
        conn.close()

    return render_template(
        'dashboard.html',
        membership_plans = plans,
        membership       = memberships,
        fitness_classes  = fitness_classes,
        workout_logs     = WORKOUT_LOGS,
        trainers         = trainers,
        message          = message
    )

# ---------------------------------------------------------------------
# Admin Dashboard (Membership + FitnessClass)
# ---------------------------------------------------------------------
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    plans           = []
    fitness_classes = []
    message         = None

    # load membership plans
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT plan_id, plan_name, duration, price FROM MembershipPlan;")
        for r in cur.fetchall():
            plans.append({"id": r[0], "name": r[1], "length": r[2], "price": r[3]})
    except Exception as e:
        message = f"Error loading plans: {e}"
    finally:
        cur.close()
        conn.close()

    # load fitness classes
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT class_id, class_name, description, schedule, capacity, trainer_id
              FROM FitnessClass
             ORDER BY class_id;
            """
        )
        for r in cur.fetchall():
            fitness_classes.append({
                "class_id":    r[0],
                "class_name":  r[1],
                "description": r[2],
                "schedule":    r[3],
                "capacity":    r[4],
                "trainer_id":  r[5]
            })
    except Exception as e:
        message = f"Error loading classes: {e}"
    finally:
        cur.close()
        conn.close()

    return render_template(
        'admin_dashboard.html',
        plans           = plans,
        fitness_classes = fitness_classes,
        error           = message
    )

# ---------------------------------------------------------------------
# MembershipPlan CRUD
# ---------------------------------------------------------------------
@app.route("/admin_dashboard/create", methods=["POST"])
def createPlan():
    name   = request.form['name']
    length = request.form['length']
    price  = request.form['price']
    if not name or not length.isdigit() or not price:
        flash("Invalid plan data", "error")
        return redirect(url_for('admin_dashboard'))
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO MembershipPlan (plan_name, duration, price) VALUES (%s, %s, %s);",
            (name, length, price)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard/delete", methods=["POST"])
def deletePlan():
    plan_id = request.form['id']
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM MembershipPlan WHERE plan_id=%s;", (plan_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard/update", methods=["POST"])
def updatePlan():
    plan_id = request.form['id']
    name    = request.form['name']
    length  = request.form['length']
    price   = request.form['price']
    if not name or not length.isdigit() or not price:
        flash("Invalid plan data", "error")
        return redirect(url_for('admin_dashboard'))
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE MembershipPlan SET plan_name=%s, duration=%s, price=%s WHERE plan_id=%s;",
            (name, length, price, plan_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

# ---------------------------------------------------------------------
# FitnessClass CRUD
# ---------------------------------------------------------------------
@app.route("/admin_dashboard/classes/create", methods=["GET", "POST"])
def create_class():
    if request.method == "POST":
        class_name  = request.form['class_name']
        description = request.form['description']
        schedule    = request.form['schedule']
        capacity    = request.form['capacity']
        trainer_id  = request.form['trainer_id']
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO FitnessClass (class_name, description, schedule, capacity, trainer_id) VALUES (%s, %s, %s, %s, %s);",
                (class_name, description, schedule, capacity, trainer_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_class_form.html', action='Create')

@app.route("/admin_dashboard/classes/<int:class_id>/edit", methods=["GET", "POST"])
def edit_class(class_id):
    if request.method == "POST":
        class_name  = request.form['class_name']
        description = request.form['description']
        schedule    = request.form['schedule']
        capacity    = request.form['capacity']
        trainer_id  = request.form['trainer_id']
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "UPDATE FitnessClass SET class_name=%s, description=%s, schedule=%s, capacity=%s, trainer_id=%s WHERE class_id=%s;",
                (class_name, description, schedule, capacity, trainer_id, class_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_dashboard'))
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT class_name, description, schedule, capacity, trainer_id FROM FitnessClass WHERE class_id=%s;",
            (class_id,)
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    if not row:
        return "Class not found", 404
    return render_template(
        'admin_class_form.html', action='Edit', class_id=class_id,
        class_name=row[0], description=row[1], schedule=row[2], capacity=row[3], trainer_id=row[4]
    )

@app.route("/admin_dashboard/classes/<int:class_id>/delete", methods=["POST"])
def delete_class(class_id):
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM FitnessClass WHERE class_id=%s;", (class_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('admin_dashboard'))

# ---------------------------------------------------------------------
# Run the app
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
