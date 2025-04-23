import psycopg2 as psy

# Database connection details
hostname = 'dpg-cvoqt3adbo4c73b7ot6g-a.oregon-postgres.render.com'
database = 'dbname_uvr7'
username = 'dbname'
pwd = 'u4TY7DucVnYJPmFjAKSgnJZsRoLCoDia'
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
