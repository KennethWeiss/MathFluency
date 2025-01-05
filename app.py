from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta
from utils.practice_tracker import PracticeTracker
from utils.math_problems import get_problem, generate_custom_multiplication
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Debug environment variables
print("=== Environment Variables ===")
for key, value in os.environ.items():
    if 'SECRET' in key.upper() or 'PASSWORD' in key.upper() or 'KEY' in key.upper():
        print(f"{key}: <hidden>")
    else:
        print(f"{key}: {value}")
print("===========================")

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    print(f"Original DATABASE_URL: {database_url}")
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print(f"Modified DATABASE_URL: {database_url}")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"Final SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
else:
    print("WARNING: No DATABASE_URL found, using SQLite")
    # For local development, use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    print(f"Using SQLite in instance folder")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure all tables exist
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # Updated to use blueprint route

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

# Import and register blueprints
from routes.auth_routes import auth_bp
from routes.layout_routes import layout_bp
from routes.main_routes import main_bp
from routes.progress_routes import progress_bp
from routes.assignment_routes import assignment_bp
from routes.practice_routes import practice_bp
from routes.class_routes import class_bp
from routes.oauth_routes import oauth_bp, google_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp

app.register_blueprint(auth_bp)
app.register_blueprint(layout_bp)
app.register_blueprint(main_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(assignment_bp)
app.register_blueprint(practice_bp)
app.register_blueprint(class_bp)
app.register_blueprint(oauth_bp, url_prefix='/oauth')
app.register_blueprint(google_bp, url_prefix='/oauth')
app.register_blueprint(admin_bp)  
app.register_blueprint(teacher_bp)

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
    app.run(debug=True)
