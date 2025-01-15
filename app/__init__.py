from flask import Flask, session, redirect, url_for, render_template
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os


# Initialize the database instance
db = SQLAlchemy()

oauth = OAuth()


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

    oauth.init_app(app)

    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        #authorize_url='https://accounts.google.com/o/oauth2/auth',
        #access_token_url='https://accounts.google.com/o/oauth2/token',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # OIDC discovery URL
        client_kwargs={'scope': 'openid profile email'},
    )

     # Import and register blueprints
    from app.routes import auth_bp  # Import the Blueprint
    
    app.register_blueprint(auth_bp)  # Register the Blueprint
    from app.upload import upload_bp  # Import the Blueprint
    
    app.register_blueprint(upload_bp)  # Register the Blueprint

    # Import models and create tables if they don't exist
    '''
    with app.app_context():
        from app.models import Login  # Import models
        db.create_all()  # Create all tables if they don't exist
        '''

    return app
