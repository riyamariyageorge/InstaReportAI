from app.db import insert_user, get_user_by_username
import bcrypt

def register_user(username, password, email):
    # Hash the password before storing it
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    insert_user(username, hashed_password.decode('utf-8'), email)

def login_user(username, password):
    # Get the user by username from the database
    user = get_user_by_username(username)
    if user:
        # Check if the password matches
        if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # user[2] is the password in DB
            return True
    return False
