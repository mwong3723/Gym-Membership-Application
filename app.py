from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2 as psy
from werkzeug.security import check_password_hash, generate_password_hash
from routes import all_blueprints
from routes import tables

# Databse info
#########################
hostname = 'dpg-cv501ql2ng1s73fl3f00-a.oregon-postgres.render.com'
database = 'gym_membership_application'
username = 'gym_membership_application_user'
pwd = '9JDl6xuzyUUZe2mbSoYfTQXxZWllT5IL'
port_id = 5432
#########################

app = Flask(__name__)
app.secret_key = "SOME_SECRET_KEY"  # Replace with a secure key in production

WORKOUT_LOGS = []  # Just appending strings here as demonstration.

MOCK_EMAIL = "user@example.com"
MOCK_PASSWORD = "password123"

for bp in all_blueprints:
    app.register_blueprint(bp)

if __name__ == "__main__": 
    tables.initTables(hostname, database, username, pwd, port_id)
    app.run(debug=True)