#from flask_sqlalchemy import SQLAlchemy
from app import db
#from datetime import datetime

    # Explicitly setting the table name to 'login'

class Login(db.Model):
    __tablename__ = 'login'  
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=True)  # Nullable for Google logins
    is_google_user = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(100), nullable=True) 

class Report(db.Model):
    __tablename__='report'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Initialize the database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Creates all tables based on models in your app