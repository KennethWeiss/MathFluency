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
    operation = request.form.get('operation', 'addition')
    level = int(request.form.get('level', 1))
    
    try:
        problem, answer = get_problem(operation, level)
        return jsonify({
            'success': True,
            'problem': problem,
            'answer': answer
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

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
        
        return render_template('progress.html',
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            accuracy=accuracy,
            avg_time=avg_time,
            fastest_correct=fastest_correct,
            current_streak=current_streak,
            operation_stats=operation_stats
        )
    except Exception as e:
        print(f"Error in progress route: {str(e)}")  # Debug print
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
