import pymysql

def get_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="sahil45",
            database="smart_farming_db",
            cursorclass=pymysql.cursors.DictCursor
        )

        return connection

    except Exception as e:
        print("Database Connection Error:", e)
        return None