import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="sql8.freesqldatabase.com",
            user="sql8833866",
            password="7ngE1JEQJN",
            database="sql8833866",
            port=3306
        )
        return conn

    except Exception as e:
        print("Database Connection Error:", e)
        return None
