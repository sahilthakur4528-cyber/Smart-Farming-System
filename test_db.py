from database import get_connection

conn = get_connection()

if conn:
    print("Database Connected Successfully!")
    conn.close()
else:
    print("Connection Failed!")