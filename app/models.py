#from flask_sqlalchemy import SQLAlchemy
from app import db
from datetime import datetime

class Login(db.Model):
    __tablename__ = 'login'  # Explicitly setting the table name to 'login'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)

# Initialize the database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Creates all tables based on models in your app