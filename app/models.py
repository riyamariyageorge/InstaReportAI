from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Login(db.Model):
    __tablename__ = 'login'  # Explicitly setting the table name to 'login'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Create tables if they do not exist
