import os
import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("sql8.freesqldatabase.com"),
            user=os.environ.get("sql8833866"),
            password=os.environ.get("7ngE1JEQJN"),
            database=os.environ.get("smart_farming_db"),
            port=int(os.environ.get("MYSQL_PORT", 3306))
        )
        return conn
    except Exception as e:
        print("Database Connection Error:", e)
        return None
