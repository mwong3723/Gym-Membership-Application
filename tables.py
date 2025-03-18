import psycopg2 as psy
gym_membership_table = '''
    CREATE TABLE IF NOT EXISTS GYM_MEMBER (
        member_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE,
        password VARCHAR(255) NOT NULL,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        phone_number VARCHAR(15), 
        register_date DATE DEFAULT CURRENT_DATE
        );
'''

membership_plan_table = '''
    CREATE TABLE IF NOT EXISTS MEMBERSHIP_PLAN (
    plan_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    membership_duration VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL
    );

'''

fitness_class_table = '''
    CREATE TABLE IF NOT EXISTS FITNESS_CLASS (
        class_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        day VARCHAR(50) NOT NULL,
        time TIME NOT NULL
    );
'''


def initTables(hostname, database, username,pwd, port_id):

    #Connect to render DB
    conn = psy.connect (
            host = hostname,
            dbname = database,
            user = username,
            password = pwd,
            port = port_id )
    cur = conn.cursor()

    #Create tables based off script
    cur.execute(gym_membership_table)
    cur.execute(membership_plan_table)
    cur.execute(fitness_class_table)
    conn.commit()
    print("Tables created")

    cur.close()
    conn.close()