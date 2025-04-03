import psycopg2 as psy

# Database connection details
hostname = 'dpg-cv501ql2ng1s73fl3f00-a.oregon-postgres.render.com'
database = 'gym_membership_application'
username = 'gym_membership_application_user'
pwd = '9JDl6xuzyUUZe2mbSoYfTQXxZWllT5IL'
port_id = 5432

# Function to connect to the database
def get_db_connection():
    try:
        conn = psy.connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
