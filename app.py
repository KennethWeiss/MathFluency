from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
from utils.practice_tracker import PracticeTracker
from utils.math_problems import get_problem, generate_custom_multiplication
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True  # Enable debug mode

db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
from routes.admin_routes import admin_bp  # New import

app.register_blueprint(auth_bp)
app.register_blueprint(layout_bp)
app.register_blueprint(main_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(assignment_bp)
app.register_blueprint(practice_bp)
app.register_blueprint(class_bp)
app.register_blueprint(oauth_bp, url_prefix='/oauth')
app.register_blueprint(google_bp, url_prefix='/oauth')
app.register_blueprint(admin_bp)  # Register admin blueprint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




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
