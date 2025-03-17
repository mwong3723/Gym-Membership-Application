from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2 as psy
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------------
# Database Connection Info
# ---------------------------------------------------------------------
hostname = 'dpg-cv501ql2ng1s73fl3f00-a.oregon-postgres.render.com'
database = 'gym_membership_application'
username = 'gym_membership_application_user'
pwd = '9JDl6xuzyUUZe2mbSoYfTQXxZWllT5IL'
port_id = 5432

# ---------------------------------------------------------------------
# Initialize Flask
# ---------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"  # Replace with a secure key in production


# ---------------------------------------------------------------------
# Ensure the GYM_MEMBER table exists (creates if not)
# ---------------------------------------------------------------------
try:
    conn = psy.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS GYM_MEMBER (
            member_id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            phone_number VARCHAR(15), 
            register_date DATE DEFAULT CURRENT_DATE
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print("Error ensuring GYM_MEMBER table exists:", e)

# ---------------------------------------------------------------------
# Mock Data (for demonstration)
# Eventually replace these with DB tables if desired
# ---------------------------------------------------------------------
MEMBERSHIP_PLANS = [
    {"id": 1, "name": "Basic Plan", "duration": "1 Month", "price": "$20"},
    {"id": 2, "name": "Premium Plan", "duration": "3 Months", "price": "$50"},
    {"id": 3, "name": "Annual Plan", "duration": "12 Months", "price": "$180"},
]

FITNESS_CLASSES = [
    {"id": 1, "name": "Yoga Class", "day": "Monday", "time": "8:00 AM"},
    {"id": 2, "name": "Spin Class", "day": "Wednesday", "time": "6:00 PM"},
    {"id": 3, "name": "HIIT Class", "day": "Friday", "time": "7:00 AM"},
]

WORKOUT_LOGS = []  # We'll store workouts in memory for now

TRAINERS = [
    {
        "id": 1,
        "name": "John Doe",
        "expertise": "Cardio, Strength",
        "availability": "Mon-Fri",
        "bio": "A seasoned trainer with 5 years of experience in cardio and strength exercises."
    },
    {
        "id": 2,
        "name": "Jane Smith",
        "expertise": "Yoga, Pilates",
        "availability": "Tue-Thu",
        "bio": "Certified yoga instructor specializing in Vinyasa and Pilates workouts."
    },
    {
        "id": 3,
        "name": "Carlos Martinez",
        "expertise": "HIIT, CrossFit",
        "availability": "Weekends",
        "bio": "Expert in high-intensity interval training and CrossFit with a focus on endurance."
    },
]


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@app.route("/")
def home():
    """ Redirect to login if not logged in; else go to dashboard. """
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """ User Registration: create an account in the GYM_MEMBER table. """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        fname = request.form.get("first_name")
        lname = request.form.get("last_name")
        phonenum = request.form.get("phone")

        hashed_password = generate_password_hash(password)

        try:
            conn = psy.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO GYM_MEMBER (email, password, first_name, last_name, phone_number)
                VALUES (%s, %s, %s, %s, %s)
            ''', (email, hashed_password, fname, lname, phonenum))
            conn.commit()
            cur.close()
            conn.close()

            return redirect(url_for("login"))
        except psy.IntegrityError:
            # Email already registered
            return render_template("register.html", error="Email is already registered.")
        except Exception as e:
            return render_template("register.html", error=f"An error occurred: {e}")

    # GET request - show the form
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ User Login: check credentials in the GYM_MEMBER table. """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = psy.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
            cur = conn.cursor()
            cur.execute("SELECT * FROM GYM_MEMBER WHERE email = %s;", (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                stored_hashed_pw = user[2]  # user = (member_id, email, password, fname, lname, phone, register_date)
                if check_password_hash(stored_hashed_pw, password):
                    session["user_email"] = email
                    return redirect(url_for("dashboard"))
                else:
                    return render_template("login.html", error="Invalid password.")
            else:
                return render_template("login.html", error="Email not found.")
        except Exception as e:
            return render_template("login.html", error=f"Error accessing database: {e}")

    # GET request - show login form
    return render_template("login.html")


@app.route("/logout")
def logout():
    """ Clear the session, then redirect to login. """
    session.pop("user_email", None)
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """
    After login, user sees a dashboard with membership selection, class booking, 
    workout logging, etc. Currently uses mock data for demonstration.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "membership":
            # [DB CODE PLACEHOLDER] e.g. update membership in real DB
            selected_plan_id = request.form.get("plan_id")
            message = f"Membership updated! (Mock) You chose plan ID = {selected_plan_id}"

        elif form_type == "book_class":
            # [DB CODE PLACEHOLDER] e.g. insert booking record into DB
            class_id = request.form.get("class_id")
            message = f"You booked class ID = {class_id} (Mock)"

        elif form_type == "log_workout":
            # [DB CODE PLACEHOLDER] e.g. insert workout log into DB
            workout_details = request.form.get("workout_details")
            WORKOUT_LOGS.append(workout_details)
            message = "Workout logged successfully! (Mock)"

    return render_template(
        "dashboard.html",
        membership_plans=MEMBERSHIP_PLANS,
        fitness_classes=FITNESS_CLASSES,
        workout_logs=WORKOUT_LOGS,
        message=message
    )


@app.route("/trainers")
def trainers():
    """
    List all trainers (mock data).
    You can replace this with a real DB table if desired.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template("trainers.html", trainers=TRAINERS)


@app.route("/trainer/<int:trainer_id>")
def trainer_detail(trainer_id):
    """
    Show detail for a single trainer (mock data).
    If you create a trainers table, you'd query the DB here.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    trainer = next((t for t in TRAINERS if t["id"] == trainer_id), None)
    if not trainer:
        return "Trainer not found.", 404

    return render_template("trainer_detail.html", trainer=trainer)


if __name__ == "__main__": 
    app.run(debug=True)
