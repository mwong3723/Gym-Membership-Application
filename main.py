import psycopg2

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

# open connection to DB

try:
    conn = psycopg2.connect(
        host = hostname,
        dbname = database,
        user = username,
        password = pwd,
        port = port_id
    )
    cur = conn.cursor()
    test_script = '''
    CREATE TABLE employee (
    ID  int primary key,
    name varchar(40) NOT NULL
    )
    '''
    cur.execute(test_script)
    conn.commit()          
except Exception as error:
    print(error)
finally:
        #Close Cursor connection
    cur.close()
    #close connection
    conn.close()