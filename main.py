import psycopg2

# Databse info
#########################
hostname = 'localhost'
database = 'postgres'
username = 'postgres'
pwd = 'gocougs25'
port_id = 5433
#########################

# open connection to DB
conn = psycopg2.connect(
    host = hostname,
    dbname = database,
    user = username,
    password = pwd,
    port = port_id
)

if conn:
    print("Works")
else:
    print("Doesn't Work")

#close connection
conn.close()