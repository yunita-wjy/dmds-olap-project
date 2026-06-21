import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    mydb = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )

    try:
        if mydb.is_connected():
            print("Connected to MySql!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    return mydb


