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

app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"  # Replace with a secure key in production

FITNESS_CLASSES = [
    {"id": 1, "name": "Yoga Class", "day": "Monday", "time": "8:00 AM"},
    {"id": 2, "name": "Spin Class", "day": "Wednesday", "time": "6:00 PM"},
    {"id": 3, "name": "HIIT Class", "day": "Friday", "time": "7:00 AM"},
]

WORKOUT_LOGS = []  # We'll store workouts in memory for now


@app.route("/add_trainer", methods=["GET", "POST"])
def add_trainer():

    if request.method == "POST":
        name = request.form.get("name")
        expertise = request.form.get("expertise")
        availability = request.form.get("availability")
        bio = request.form.get("bio")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO TRAINER (name, expertise, availability, bio)
                VALUES (%s, %s, %s, %s)
            ''', (name, expertise, availability, bio))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("trainer_list"))
        except Exception as e:
            return f"Error inserting trainer: {e}"

    return render_template("add_trainer.html")

@app.route("/trainers")
def trainer_list():
    if "user_email" not in session:
        return redirect(url_for("login"))

    try:
        conn = psy.connect(
            host=hostname, 
            dbname=database, 
            user=username, 
            password=pwd, 
            port=port_id
        )
        cur = conn.cursor()
        
        # If your table is quoted uppercase, do this:
        cur.execute('SELECT trainer_id, name, expertise, availability, bio FROM "TRAINER";')
        
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
                "availability": row[3],
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
        conn = psy.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cur = conn.cursor()
        cur.execute("SELECT trainer_id, name, expertise, availability, bio FROM TRAINER WHERE trainer_id = %s;", (trainer_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            return "Trainer not found", 404

        trainer = {
            "trainer_id": row[0],
            "name": row[1],
            "expertise": row[2],
            "availability": row[3],
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
    """ User Registration: create an account in the GYM_MEMBER table. """
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
    trainers = []
    memberships = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * from Trainer;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            trainers.append({
                "trainer_id": row[0],
                "name": row[1],
                "expertise": row[2],
                "contact_info": row[3]
            })

    except Exception as e:
        message = f"Error fetching trainers: {e}"

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
            trainers=trainers,  # pass trainer info if you want to display it
            message=message
        )

@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    plans = []
    message = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM MembershipPlan")
        data = cur.fetchall()
        cur.close()
        conn.close()

        for row in data:
            plans.append({
                "id": row[0],
                "name": row[1],
                "length": row[2],
                "price": row[3]
            })
        
    except Exception as e:
        message=f"Error accessing database: {e}"
    
    return render_template("admin_dashboard.html", plans=plans, error=message)

@app.route("/admin_dashboard/create", methods=["GET","POST"])
def createPlan():
    if request.method == "POST":
        name = request.form.get("name")
        length = request.form.get("length")
        price = request.form.get("price")

        if not name:
            flash("Plan name cannot be left empty", "error")
            return redirect(url_for('admin_dashboard'))

        
        if not length or not length.isdigit():
            flash("Duration must be an integer", "error")
            return redirect(url_for('admin_dashboard'))
        
        if not price:
            flash("Price must be a valid number", "error")
            return redirect(url_for('admin_dashboard'))
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                    INSERT INTO MembershipPlan (plan_name, duration, price)
                    VALUES (%s, %s, %s)
                ''', (name, length, price))
            conn.commit()
            cur.close()
            conn.close()
        
        except Exception as e:
            print(f"Error with database: {e}")
        
        return redirect(url_for('admin_dashboard'))

@app.route("/admin_dashboard/delete", methods=["GET","POST"])
def deletePlan():
    if request.method == "POST":
        id = request.form.get("id")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''DELETE FROM MembershipPlan where plan_id = %s''', (id,))
            conn.commit()
            cur.close()
            conn.close()
        
        except Exception as e:
            print(f"Error with database: {e}")
            print(f"The id retrived is: {id}")
        
        return redirect(url_for('admin_dashboard'))
    
@app.route("/admin_dashboard/update", methods=["GET","POST"])
def updatePlan():
    if request.method == "POST":
        id = request.form.get("id")
        name = request.form.get("name")
        length = request.form.get("length")
        price = request.form.get("price")

        if not name:
            flash("Plan name cannot be left empty", "error")
            return redirect(url_for('admin_dashboard'))

        
        if not length or not length.isdigit():
            flash("Duration must be an integer", "error")
            return redirect(url_for('admin_dashboard'))
        
        if not price:
            flash("Price must be a valid number", "error")
            return redirect(url_for('admin_dashboard'))
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                '''UPDATE MembershipPlan SET plan_name=%s, duration=%s, price=%s where plan_id=%s''', 
                (name, length, price, id,))
            conn.commit()
            cur.close()
            conn.close()
        
        except Exception as e:
            print(f"Error with database: {e}")
        
        return redirect(url_for('admin_dashboard'))

    
if __name__ == "__main__": 
    tables.initTables(hostname, database, username, pwd, port_id)
    app.run(debug=True)