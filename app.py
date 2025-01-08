import os
from dotenv import load_dotenv
import logging

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta
from utils.practice_tracker import PracticeTracker
from utils.math_problems import get_problem, generate_custom_multiplication
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Debug before loading .env
logger.debug("Before load_dotenv:")
logger.debug(f"GOOGLE_CLIENT_ID exists: {os.environ.get('GOOGLE_CLIENT_ID') is not None}")


# Load .env file if it exists
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    logger.debug(f".env file found at {env_path}")
    load_dotenv(env_path)
else:
    logger.debug("No .env file found, using system environment variables")

# Debug after loading .env
logger.debug("After load_dotenv:")
logger.debug(f"GOOGLE_CLIENT_ID exists: {os.environ.get('GOOGLE_CLIENT_ID') is not None}")
logger.debug(f"All environment variables: {list(os.environ.keys())}")

# Allow OAuth over HTTP for local development
if os.environ.get('FLASK_ENV') != 'production':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configure Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

# Only use secure cookies in production
if not app.debug:
    app.config['SESSION_COOKIE_SECURE'] = True

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fluency.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from models import db, init_db
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Import and initialize SocketIO
from extensions import socketio
socketio.init_app(app, cors_allowed_origins="*")

# Import WebSocket handlers after SocketIO initialization
from websockets.quiz import *

# OAuth settings
logger.debug("Configuring OAuth settings")
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
logger.debug(f"GOOGLE_CLIENT_ID exists: {client_id is not None}")
logger.debug(f"GOOGLE_CLIENT_SECRET exists: {client_secret is not None}")
logger.debug(f"GOOGLE_CLIENT_ID length: {len(client_id) if client_id else 0}")
logger.debug(f"GOOGLE_CLIENT_SECRET length: {len(client_secret) if client_secret else 0}")
app.config.update(
        GOOGLE_OAUTH_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID"),
        GOOGLE_OAUTH_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET")
    )

# Ensure all tables exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Add this after app initialization but before routes
@app.template_filter('unique')
def unique_filter(l):
    """Return unique items from a list while preserving order"""
    seen = set()
    return [x for x in l if not (x in seen or seen.add(x))]

# Import models after db initialization
from models.user import User
from models.class_ import Class
from models.practice_attempt import PracticeAttempt
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from models.quiz import Quiz, QuizParticipant, QuizQuestion

# Import blueprints
from routes.auth_routes import auth_bp
from routes.layout_routes import layout_bp
from routes.main_routes import main_bp
from routes.class_routes import class_bp
from routes.assignment_routes import assignment_bp
from routes.practice_routes import practice_bp
from routes.oauth_routes import oauth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.oauth_routes import blueprint as google_blueprint
from routes.progress_routes import progress_bp
from routes.quiz_routes import quiz_bp

# Register blueprints
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.class_routes import class_bp
from routes.quiz_routes import quiz_bp
from routes.teacher_routes import teacher_bp
from routes.practice_routes import practice_bp
from routes.oauth_routes import oauth_bp, blueprint as google_blueprint

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(class_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(practice_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(google_blueprint, url_prefix="/oauth")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.cli.command("reset-db")
def reset_db():
    """Reset the database by dropping and recreating all tables."""
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Stamping alembic version...")
    from flask_migrate import stamp
    # Get the migration directory
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
    # Get the latest revision file
    revision_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
    if revision_files:
        latest_revision = revision_files[0].split('_')[0]
        print(f"Stamping with revision: {latest_revision}")
        stamp(revision=latest_revision)
    else:
        print("No revision files found")
    print("Database reset complete!")

@app.template_filter('timeago')
def timeago(date):
    """Convert a datetime to a time ago string."""
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "just now"

def calculate_difficulty_level(user_id, operation, current_level):
    """Calculate the appropriate difficulty level based on user performance."""
    # Get recent attempts (last 10) for the current level
    recent_attempts = PracticeAttempt.query.filter_by(
        user_id=user_id,
        operation=operation,
        level=current_level
    ).order_by(PracticeAttempt.created_at.desc()).limit(10).all()
    
    if not recent_attempts:
        return current_level
    
    # Calculate success rate
    correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)
    success_rate = correct_count / len(recent_attempts)
    
    # Get average time for correct attempts
    correct_times = [a.time_taken for a in recent_attempts if a.is_correct and a.time_taken]
    avg_time = sum(correct_times) / len(correct_times) if correct_times else float('inf')
    
    # Decision logic for level adjustment
    if success_rate >= 0.9 and avg_time < 5.0:  # 90% accuracy and under 5 seconds
        return min(current_level + 1, 5 if operation == 'addition' else 12)
    elif success_rate < 0.7:  # Less than 70% accuracy
        return max(current_level - 1, 1)
    
    return current_level

@app.route('/record_attempt', methods=['POST'])
@login_required
def record_attempt():
    data = request.json
    attempt = PracticeAttempt(
        user_id=current_user.id,
        operation=data['operation'],
        level=data['level'],
        problem=data['problem'],
        user_answer=data['userAnswer'],
        correct_answer=data['correctAnswer'],
        is_correct=data['isCorrect'],
        time_taken=data.get('timeTaken')
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
