
import psycopg2 as psy

member_table = '''
CREATE TABLE IF NOT EXISTS Member (
    member_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone VARCHAR(20),
    registration_date DATE DEFAULT CURRENT_DATE
);
'''

membership_plan_table = '''
CREATE TABLE IF NOT EXISTS MembershipPlan (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(255) NOT NULL,
    duration INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT
);
'''

membership_table = '''
CREATE TABLE IF NOT EXISTS Membership (
    member_id INT NOT NULL,
    plan_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) CHECK (status IN ('active', 'canceled', 'renewed')),
    PRIMARY KEY (member_id, plan_id),
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES MembershipPlan(plan_id)
);
'''

trainer_table = '''
CREATE TABLE IF NOT EXISTS Trainer (
    trainer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    expertise TEXT,
    contact_info TEXT,
    description TEXT
);
'''

fitness_class_table = '''
CREATE TABLE IF NOT EXISTS FitnessClass (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule TIMESTAMP NOT NULL,
    capacity INT NOT NULL,
    trainer_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE SET NULL
);
'''

booking_table = '''
CREATE TABLE IF NOT EXISTS Booking (
    member_id INT NOT NULL,
    class_id INT NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('confirmed', 'cancelled')),
    PRIMARY KEY (member_id, class_id),
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES FitnessClass(class_id) ON DELETE CASCADE
);
'''

workout_log_table = '''
CREATE TABLE IF NOT EXISTS WorkoutLog (
    log_id SERIAL PRIMARY KEY,
    member_id INT NOT NULL,
    workout_date DATE NOT NULL,
    workout_details TEXT NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE
);
'''

admin_table = '''
CREATE TABLE IF NOT EXISTS Admin (
    admin_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL
);
'''

admin_trainer_table = '''
CREATE TABLE IF NOT EXISTS Admin_Trainer (
    admin_id INT NOT NULL,
    trainer_id INT NOT NULL,
    PRIMARY KEY (admin_id, trainer_id),
    FOREIGN KEY (admin_id) REFERENCES Admin(admin_id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id) ON DELETE CASCADE
);
'''

admin_class_table = '''
CREATE TABLE IF NOT EXISTS Admin_Class (
    admin_id INT NOT NULL,
    class_id INT NOT NULL,
    PRIMARY KEY (admin_id, class_id),
    FOREIGN KEY (admin_id) REFERENCES Admin(admin_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES FitnessClass(class_id) ON DELETE CASCADE
);
'''

delete_tables_script = '''
DROP TABLE IF EXISTS 
    Admin_Class, 
    Admin_Trainer, 
    Admin, 
    WorkoutLog, 
    Booking, 
    FitnessClass, 
    Trainer, 
    Membership, 
    MembershipPlan, 
    Member 
CASCADE;
'''

def deleteTables(hostname, database, username,pwd, port_id):
    #Connect to render DB
    conn = psy.connect (
            host = hostname,
            dbname = database,
            user = username,
            password = pwd,
            port = port_id )
    cur = conn.cursor()

    #Create tables based off script
    cur.execute(delete_tables_script)
    conn.commit()
    print("Tables deleted")

    cur.close()
    conn.close()

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
    cur.execute(member_table)
    cur.execute(membership_plan_table)
    cur.execute(membership_table)
    cur.execute(trainer_table)
    cur.execute(fitness_class_table)
    cur.execute(booking_table)
    cur.execute(workout_log_table)
    cur.execute(admin_table)
    cur.execute(admin_trainer_table)
    cur.execute(admin_class_table )
    conn.commit()
    print("Tables created")

    cur.close()
    conn.close()

def get_db_connection():
    """Creates a connection to the database."""
    return psy.connect(host=hostname, dbname=database, user=username, password=password, port=port_id)