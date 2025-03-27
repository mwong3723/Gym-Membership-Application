from flask import Blueprint, redirect, url_for, session

home_bp = Blueprint("home", __name__)

# ---------------------------------------------------------------------
# Home / Register / Login / Logout
# ---------------------------------------------------------------------
@app.route("/")
def home():
    """ Redirect to login if not logged in; else go to dashboard. """
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """
    After login, user sees a dashboard with membership selection, class booking, 
    workout logging, etc. Currently uses mock data for demonstration.
    
    We'll also fetch TRAINER data from DB to display on the dashboard if needed.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    message = None

    if request.method == "POST":
        form_type = request.form.get("form_type")

        if form_type == "membership":
            selected_plan_id = request.form.get("plan_id")
            message = f"Membership updated! (Mock) You chose plan ID = {selected_plan_id}"

        elif form_type == "book_class":
            class_id = request.form.get("class_id")
            message = f"You booked class ID = {class_id} (Mock)"

        elif form_type == "log_workout":
            workout_details = request.form.get("workout_details")
            WORKOUT_LOGS.append(workout_details)
            message = "Workout logged successfully! (Mock)"

    # -----------------------------------------------------------------
    # OPTIONAL: If you want to show trainers on the dashboard, fetch them:
    # -----------------------------------------------------------------
    trainers = []
    try:
        conn = psy.connect(host=hostname, dbname=database, user=username, password=pwd, port=port_id)
        cur = conn.cursor()
        cur.execute("SELECT trainer_id, name, expertise, availability, bio FROM TRAINER;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            trainers.append({
                "trainer_id": row[0],
                "name": row[1],
                "expertise": row[2],
                "availability": row[3],
                "bio": row[4]
            })
    except Exception as e:
        message = f"Error fetching trainers: {e}"

    return render_template(
        "dashboard.html",
        membership_plans=MEMBERSHIP_PLANS,
        fitness_classes=FITNESS_CLASSES,
        workout_logs=WORKOUT_LOGS,
        trainers=trainers,  # pass trainer info if you want to display it
        message=message
    )