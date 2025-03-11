from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2 as psy

# Databse info
#########################
hostname = 'dpg-cv501ql2ng1s73fl3f00-a.oregon-postgres.render.com'
database = 'gym_membership_application'
username = 'gym_membership_application_user'
pwd = '9JDl6xuzyUUZe2mbSoYfTQXxZWllT5IL'
port_id = 5432
#########################

conn = None
cur = None 



app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"  # Replace with a secure key in production


def setup():
    membership_plan_create_table_script = '''
    CREATE TABLE IF NOT EXISTS MEMBERSHIP_PLANS (
    plan_id NUMBER PRIMARY KEY,
    plan_name VARCHAR2(255) NOT NULL,
    membership_duration INTERVAL DAY TO SECOND NOT NULL,
    price NUMBER NOT NULL
    );
    '''
    
    if(cur.execute(membership_plan_create_table_script)):
        print("Membership plan table create")
    else:
        print("Did not create membership plan table")



# ---------------------------------------------------------------------
# MOCK DATA (No Real DB Yet!)
# ---------------------------------------------------------------------
# [DB CODE PLACEHOLDER]: Once you have your DB, remove these lists and
#   replace them with actual queries that fetch data from PostgreSQL.
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

WORKOUT_LOGS = []  # Just appending strings here as demonstration.

# [DB CODE PLACEHOLDER]: Replace with real user check or remove once integrated
MOCK_EMAIL = "user@example.com"
MOCK_PASSWORD = "password123"


@app.route("/")
def home():
    # If user is already "logged in", go straight to dashboard.
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    This is a simplified login page.
    Later, you'll likely do:
    1) Check user from the DB
    2) Validate password (hashed)
    3) Set session
    """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # [DB CODE PLACEHOLDER]:
        #   Replace the following lines with your DB user lookup
        #   user = User.query.filter_by(email=email).first()
        #   if user and check_password(user.password, password):
        #       session["user_id"] = user.id
        #       ...

        if email == MOCK_EMAIL and password == MOCK_PASSWORD:
            session["user_email"] = email  # Mock "logged in"
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials. Try again.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """
    After-login page.
    Shows membership selection, class booking, workout logging, etc.
    Currently uses in-memory data to demonstrate the UI.
    Later, you'll add real DB queries & updates.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    # [DB CODE PLACEHOLDER]:
    #   Possibly fetch the user's current membership from DB
    #   membership = query_from_db(session["user_email"])
    #   For now, we just show a blank or mock membership scenario.

    message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "membership":
            # [DB CODE PLACEHOLDER]:
            #   e.g., "UPDATE membership SET plan_id=... WHERE user_id=..."
            selected_plan_id = request.form.get("plan_id")
            message = f"Membership updated! (Mock) You chose plan ID = {selected_plan_id}"

        elif form_type == "book_class":
            # [DB CODE PLACEHOLDER]:
            #   e.g., "INSERT INTO bookings(user_id, class_id) VALUES(...)"
            class_id = request.form.get("class_id")
            message = f"You booked class ID = {class_id} (Mock)"

        elif form_type == "log_workout":
            # [DB CODE PLACEHOLDER]:
            #   e.g., "INSERT INTO workout_logs(user_id, details, date) VALUES(...)"
            workout_details = request.form.get("workout_details")
            WORKOUT_LOGS.append(workout_details)  # Just appending to a list in memory
            message = "Workout logged successfully! (Mock)"

    return render_template(
        "dashboard.html",
        membership_plans=MEMBERSHIP_PLANS,  # [DB CODE PLACEHOLDER]: fetch from DB
        fitness_classes=FITNESS_CLASSES,    # [DB CODE PLACEHOLDER]: fetch from DB
        workout_logs=WORKOUT_LOGS,          # [DB CODE PLACEHOLDER]: fetch from DB
        message=message
    )



if __name__ == "__main__":
    conn = psy.connect(
        host = hostname,
        dbname = database,
        user = username,
        password = pwd,
        port = port_id
    )

    setup()
    app.run(debug=True)

    conn.close()