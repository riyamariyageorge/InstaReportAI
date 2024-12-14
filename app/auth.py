from app.models import Login, db
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, password, email):
     # Hash the password before saving it to the database
    hashed_password = generate_password_hash(password)
    new_user = Login(username=username, password=hashed_password, email=email)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        return False

def login_user(username, password):
    user = Login.query.filter_by(username=username).first()  # Get user by username
    if user and check_password_hash(user.password, password):  # Compare hashed password
        return True
    return False
