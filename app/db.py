import psycopg2
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get PostgreSQL connection details from .env file
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    return connection

def insert_user(username, password, email):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO login (username, password, user_email) VALUES (%s, %s, %s)",
            (username, password, email)
        )
        connection.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def get_user_by_username(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM login WHERE username = %s", (username,))
        user = cursor.fetchone()  # Fetch one user from DB
        return user
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
'''
def authenticate_user(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT password FROM login WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            stored_hashed_password = user[0]  # Assuming password is stored as first column
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                return True  # Authentication successful
            else:
                return False  # Incorrect password
        else:
            return False  # User not found
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()
    '''