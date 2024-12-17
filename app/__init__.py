from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Initialize the database instance
db = SQLAlchemy()

def create_app():
    # Load environment variables
    load_dotenv()
     # Initialize the Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("SECRET_KEY")

    # Initialize the database with the app
    db.init_app(app)

     # Import and register blueprints
    from app.routes import auth_bp  # Import the Blueprint
    from app.upload import upload_bp
    app.register_blueprint(auth_bp)  # Register the Blueprint
    app.register_blueprint(upload_bp)

    # Import models and create tables if they don't exist
    '''
    with app.app_context():
        from app.models import Login  # Import models
        db.create_all()  # Create all tables if they don't exist
        '''

    return app
