from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
from utils.problem_generator import get_problem
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True  # Enable debug mode

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

# Debug print to see which models are loaded
print("Models loaded:", [User.__name__, Class.__name__, PracticeAttempt.__name__])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('welcome'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_teacher=False  # By default, new registrations are students
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

@app.route('/welcome')
@login_required
def welcome():
    try:
        if current_user.is_teacher:
            # For teachers, show their classes and students
            classes = current_user.classes.all()
            students = current_user.students.all()
            return render_template('welcome.html', 
                                classes=classes, 
                                students=students, 
                                is_teacher=True)
        else:
            # For students, show their class and teacher
            return render_template('welcome.html', 
                                enrolled_class=current_user.enrolled_class,
                                is_teacher=False)
    except Exception as e:
        print(f"Error in welcome route: {str(e)}")  # This will print to console
        flash(f"An error occurred: {str(e)}", 'danger')  # This will show to user
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/practice')
@login_required
def practice():
    print("In practice route")
    return render_template('practice.html')

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

@app.route('/get_problem', methods=['POST'])
@login_required
def get_problem_route():
    try:
        data = request.get_json()
        operation = data.get('operation')
        level = int(data.get('level', 1))
        
        if operation not in ['addition', 'multiplication']:
            return jsonify({'error': 'Invalid operation'}), 400
        
        # Calculate appropriate difficulty level
        adapted_level = calculate_difficulty_level(current_user.id, operation, level)
        
        # Get problem with user history consideration
        problem = get_problem(operation, adapted_level, current_user.id, db)
        
        return jsonify({
            'problem': problem['problem'],
            'level': adapted_level,
            'operation': operation
        })
    except Exception as e:
        print(f"Error in get_problem route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    user_answer = request.form.get('answer')
    correct_answer = request.form.get('correct_answer')
    
    try:
        is_correct = int(user_answer) == int(correct_answer)
        return jsonify({
            'success': True,
            'is_correct': is_correct
        })
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Invalid answer format'
        }), 400

def get_problem_history(user_id, operation=None, limit=10):
    """Get recent problem history for a user, optionally filtered by operation."""
    query = PracticeAttempt.query.filter_by(user_id=user_id)
    if operation:
        query = query.filter_by(operation=operation)
    return query.order_by(PracticeAttempt.created_at.desc()).limit(limit).all()

def analyze_missed_problems(user_id, operation=None):
    """Analyze commonly missed problems for a user."""
    # Get all attempts for the user
    query = PracticeAttempt.query.filter_by(user_id=user_id, is_correct=False)
    if operation:
        query = query.filter_by(operation=operation)
    
    missed_attempts = query.all()
    problem_stats = {}
    
    for attempt in missed_attempts:
        if attempt.problem not in problem_stats:
            problem_stats[attempt.problem] = {
                'total_attempts': 0,
                'incorrect_attempts': 0,
                'last_seen': attempt.created_at,
                'operation': attempt.operation,
                'level': attempt.level
            }
        
        problem_stats[attempt.problem]['total_attempts'] += 1
        problem_stats[attempt.problem]['incorrect_attempts'] += 1
        
        # Update last seen if this attempt is more recent
        if attempt.created_at > problem_stats[attempt.problem]['last_seen']:
            problem_stats[attempt.problem]['last_seen'] = attempt.created_at
    
    # Convert to list and sort by incorrect attempts
    problem_list = [
        {
            'problem': problem,
            'total_attempts': stats['total_attempts'],
            'incorrect_attempts': stats['incorrect_attempts'],
            'last_seen': stats['last_seen'],
            'operation': stats['operation'],
            'level': stats['level']
        }
        for problem, stats in problem_stats.items()
    ]
    
    return sorted(problem_list, key=lambda x: x['incorrect_attempts'], reverse=True)

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

@app.route('/progress')
@login_required
def progress():
    try:
        # Get total attempts for this user
        total_attempts = PracticeAttempt.query.filter_by(user_id=current_user.id).count()
        print(f"Total attempts: {total_attempts}")  # Debug print
        
        # Get correct attempts and calculate accuracy
        correct_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id, 
            is_correct=True
        ).count()
        print(f"Correct attempts: {correct_attempts}")  # Debug print
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get average time taken
        avg_time = db.session.query(func.avg(PracticeAttempt.time_taken))\
            .filter(PracticeAttempt.user_id == current_user.id).scalar() or 0
        print(f"Average time: {avg_time}")  # Debug print
        
        # Get fastest correct attempt
        fastest_correct = PracticeAttempt.query\
            .filter_by(user_id=current_user.id, is_correct=True)\
            .order_by(PracticeAttempt.time_taken.asc()).first()
        
        # Get current streak
        attempts = PracticeAttempt.query\
            .filter_by(user_id=current_user.id)\
            .order_by(PracticeAttempt.created_at.desc()).all()
        current_streak = 0
        for attempt in attempts:
            if attempt.is_correct:
                current_streak += 1
            else:
                break
        
        # Get operation-specific stats with level details
        operation_stats = {}
        
        # Addition levels
        addition_levels = {
            1: "Adding 1 to single digit",
            2: "Adding 2 to single digit",
            3: "Make 10",
            4: "Add single digit to double digit",
            5: "Add double digit to double digit"
        }
        
        # Multiplication levels (tables)
        multiplication_levels = {i: f"× {i} Table" for i in range(13)}  # 0-12 tables
        
        # Get stats for addition levels
        addition_stats = {}
        addition_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id,
            operation='addition'
        ).all()
        print(f"Addition attempts found: {len(addition_attempts)}")  # Debug print
        
        if addition_attempts:
            for level, description in addition_levels.items():
                level_attempts = [a for a in addition_attempts if a.level == level]
                total = len(level_attempts)
                print(f"Level {level} attempts: {total}")  # Debug print
                if total > 0:
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    
                    addition_stats[str(level)] = {  # Convert level to string for template
                        'description': description,
                        'total': total,
                        'accuracy': (correct/total*100),
                        'avg_time': avg_time
                    }
        
        # Get stats for multiplication levels
        multiplication_stats = {}
        multiplication_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id,
            operation='multiplication'
        ).all()
        print(f"Multiplication attempts found: {len(multiplication_attempts)}")  # Debug print
        
        if multiplication_attempts:
            for level, description in multiplication_levels.items():
                level_attempts = [a for a in multiplication_attempts if a.level == level]
                total = len(level_attempts)
                print(f"Table {level} attempts: {total}")  # Debug print
                if total > 0:
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    
                    multiplication_stats[str(level)] = {  # Convert level to string for template
                        'description': description,
                        'total': total,
                        'accuracy': (correct/total*100),
                        'avg_time': avg_time
                    }
        
        operation_stats = {
            'addition': addition_stats,
            'multiplication': multiplication_stats
        }
        print(f"Final operation_stats: {operation_stats}")  # Debug print
        
        # Add missed problems analysis
        addition_missed = analyze_missed_problems(current_user.id, 'addition')
        multiplication_missed = analyze_missed_problems(current_user.id, 'multiplication')
        
        return render_template('progress.html',
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            accuracy=accuracy,
            avg_time=avg_time,
            fastest_correct=fastest_correct,
            current_streak=current_streak,
            operation_stats=operation_stats,
            addition_missed=addition_missed[:5],  # Show top 5 missed problems
            multiplication_missed=multiplication_missed[:5]
        )
    except Exception as e:
        print(f"Error in progress route: {str(e)}")  # Debug print
        return f"An error occurred: {str(e)}", 500

@app.route('/analyze_level/<operation>/<int:level>')
@login_required
def analyze_level(operation, level):
    try:
        # Get all attempts for this level
        attempts = PracticeAttempt.query.filter(
            PracticeAttempt.user_id == current_user.id,
            PracticeAttempt.operation == operation,
            PracticeAttempt.level == level
        ).order_by(PracticeAttempt.created_at.desc()).all()
        
        # Analyze the attempts
        total_attempts = len(attempts)
        incorrect_attempts = [a for a in attempts if not a.is_correct]
        
        # Group incorrect attempts by problem
        problem_stats = {}
        for attempt in incorrect_attempts:
            if attempt.problem not in problem_stats:
                problem_stats[attempt.problem] = {
                    'incorrect_count': 0,
                    'user_answers': [],
                    'correct_answer': attempt.correct_answer
                }
            problem_stats[attempt.problem]['incorrect_count'] += 1
            problem_stats[attempt.problem]['user_answers'].append(attempt.user_answer)
        
        # Convert to list and sort by incorrect count
        problems_list = [
            {
                'problem': problem,
                'incorrect_count': stats['incorrect_count'],
                'user_answers': stats['user_answers'],
                'correct_answer': stats['correct_answer']
            }
            for problem, stats in problem_stats.items()
        ]
        problems_list.sort(key=lambda x: x['incorrect_count'], reverse=True)
        
        # Calculate overall statistics
        accuracy = ((total_attempts - len(incorrect_attempts)) / total_attempts * 100) if total_attempts > 0 else 0
        
        return render_template('analyze_level.html',
            operation=operation,
            level=level,
            total_attempts=total_attempts,
            incorrect_count=len(incorrect_attempts),
            accuracy=accuracy,
            problems=problems_list
        )
        
    except Exception as e:
        print(f"Error in analyze_level route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/incorrect_problems')
@login_required
def incorrect_problems():
    # Get incorrect attempts for the current user
    incorrect_attempts = PracticeAttempt.query.filter_by(
        user_id=current_user.id,
        is_correct=False
    ).order_by(PracticeAttempt.created_at.desc()).all()
    
    return render_template('incorrect_problems.html', attempts=incorrect_attempts)

if __name__ == '__main__':
    app.run(debug=True)
