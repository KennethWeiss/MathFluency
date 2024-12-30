from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from forms import LoginForm, RegistrationForm
from utils.problem_generator import ProblemGenerator
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

# Import and register blueprints
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route('/welcome')
@login_required
def welcome():
    if current_user.is_teacher:
        # Get all students for this teacher
        students = current_user.students
        classes = current_user.classes
        return render_template('welcome.html', 
                            is_teacher=True,
                            students=students,
                            classes=classes)
    else:
        # Get the student's enrolled class
        enrolled_class = current_user.enrolled_class
        return render_template('welcome.html',
                            is_teacher=False,
                            enrolled_class=enrolled_class)

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
    """Get a new problem based on user's history and mastery level."""
    try:
        data = request.json
        print(f"\nReceived request data: {data}")  # Debug log
        
        operation = data.get('operation')
        level = data.get('level')
        
        print(f"Operation: {operation}, Level: {level}")  # Debug log
        
        if not operation or level is None:
            print(f"Missing data: operation={operation}, level={level}")  # Debug log
            return jsonify({'error': 'Missing operation or level'}), 400
        
        try:
            level = int(level)
        except (TypeError, ValueError) as e:
            print(f"Error converting level to int: {e}")  # Debug log
            return jsonify({'error': 'Invalid level format'}), 400
            
        # Use ProblemGenerator.get_problem instead of get_problem
        print(f"Calling ProblemGenerator.get_problem with: operation={operation}, level={level}")  # Debug log
        problem = ProblemGenerator.get_problem(
            operation=operation,
            level=level,
            user_id=current_user.id,
            db=db
        )
        
        print(f"Generated problem: {problem}")  # Debug log
        return jsonify(problem)
        
    except Exception as e:
        print(f"Error generating problem: {str(e)}")  # Detailed error log
        import traceback
        print(traceback.format_exc())  # Print full stack trace
        return jsonify({'error': 'Error generating problem'}), 500

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
        # If viewing as teacher with student_id parameter, redirect to student_progress
        student_id = request.args.get('student_id')
        if current_user.is_teacher and student_id:
            return redirect(url_for('student_progress', student_id=student_id))
            
        # Get total attempts for this user
        total_attempts = PracticeAttempt.query.filter_by(user_id=current_user.id).count()
        print(f"Total attempts: {total_attempts}")  # Debug print
        
        # Get correct attempts and calculate accuracy
        correct_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id, 
            is_correct=True
        ).count()
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        print(f"Accuracy: {accuracy}%")  # Debug print
        
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
        
        if addition_attempts:
            addition_total = len(addition_attempts)
            addition_correct = len([a for a in addition_attempts if a.is_correct])
            addition_accuracy = (addition_correct / addition_total * 100) if addition_total > 0 else 0
            addition_times = [a.time_taken for a in addition_attempts if a.time_taken is not None]
            addition_avg_time = sum(addition_times) / len(addition_times) if addition_times else 0
            
            # Get level-specific stats
            for level, description in addition_levels.items():
                level_attempts = [a for a in addition_attempts if a.level == level]
                if level_attempts:
                    total = len(level_attempts)
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    accuracy = (correct / total * 100) if total > 0 else 0
                    
                    # Determine mastery status
                    mastery_status = 'needs_practice'
                    if total >= PracticeAttempt.MIN_ATTEMPTS:
                        if (correct / total) >= PracticeAttempt.MASTERY_THRESHOLD:
                            mastery_status = 'mastered'
                        elif (correct / total) >= PracticeAttempt.LEARNING_THRESHOLD:
                            mastery_status = 'learning'
                    
                    addition_stats[str(level)] = {
                        'description': description,
                        'attempts': total,
                        'accuracy': accuracy,
                        'avg_time': avg_time,
                        'mastery_status': mastery_status
                    }
                    print(f"Level {level} stats:", addition_stats[str(level)])  # Debug print
            
            operation_stats['addition'] = {
                'total_attempts': addition_total,
                'accuracy': addition_accuracy,
                'current_streak': current_streak,
                'levels': addition_stats
            }
        
        # Get stats for multiplication levels
        multiplication_stats = {}
        multiplication_attempts = PracticeAttempt.query.filter_by(
            user_id=current_user.id,
            operation='multiplication'
        ).all()
        
        if multiplication_attempts:
            mult_total = len(multiplication_attempts)
            mult_correct = len([a for a in multiplication_attempts if a.is_correct])
            mult_accuracy = (mult_correct / mult_total * 100) if mult_total > 0 else 0
            mult_times = [a.time_taken for a in multiplication_attempts if a.time_taken is not None]
            mult_avg_time = sum(mult_times) / len(mult_times) if mult_times else 0
            
            # Get level-specific stats
            for level, description in multiplication_levels.items():
                level_attempts = [a for a in multiplication_attempts if a.level == level]
                if level_attempts:
                    total = len(level_attempts)
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    accuracy = (correct / total * 100) if total > 0 else 0
                    
                    # Determine mastery status
                    mastery_status = 'needs_practice'
                    if total >= PracticeAttempt.MIN_ATTEMPTS:
                        if (correct / total) >= PracticeAttempt.MASTERY_THRESHOLD:
                            mastery_status = 'mastered'
                        elif (correct / total) >= PracticeAttempt.LEARNING_THRESHOLD:
                            mastery_status = 'learning'
                    
                    multiplication_stats[str(level)] = {
                        'description': description,
                        'attempts': total,
                        'accuracy': accuracy,
                        'avg_time': avg_time,
                        'mastery_status': mastery_status
                    }
            
            operation_stats['multiplication'] = {
                'total_attempts': mult_total,
                'accuracy': mult_accuracy,
                'current_streak': current_streak,
                'levels': multiplication_stats
            }
        
        return render_template('progress.html', 
                            stats=operation_stats,
                            viewing_as_teacher=False)
                            
    except Exception as e:
        print(f"Error in progress route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading progress data.', 'danger')
        return redirect(url_for('welcome'))

@app.route('/student_progress/<int:student_id>')
@login_required
def student_progress(student_id):
    """View progress for a specific student (teacher only)"""
    try:
        # Verify current user is a teacher
        if not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('welcome'))
        
        # Get the student
        student = User.query.get_or_404(student_id)
        
        # Verify student belongs to this teacher
        if student.teacher_id != current_user.id:
            flash('Access denied. Not your student.', 'danger')
            return redirect(url_for('welcome'))
        
        # Get operation-specific stats
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
        
        # Get addition stats
        addition_attempts = PracticeAttempt.query.filter_by(
            user_id=student_id,
            operation='addition'
        ).all()
        
        if addition_attempts:
            total = len(addition_attempts)
            correct = len([a for a in addition_attempts if a.is_correct])
            accuracy = (correct / total * 100) if total > 0 else 0
            
            # Calculate current streak
            current_streak = 0
            for attempt in sorted(addition_attempts, key=lambda x: x.created_at, reverse=True):
                if attempt.is_correct:
                    current_streak += 1
                else:
                    break
            
            # Get level-specific stats
            addition_stats = {}
            for level, description in addition_levels.items():
                level_attempts = [a for a in addition_attempts if a.level == level]
                if level_attempts:
                    total = len(level_attempts)
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    accuracy = (correct / total * 100) if total > 0 else 0
                    
                    # Determine mastery status
                    mastery_status = 'needs_practice'
                    if total >= PracticeAttempt.MIN_ATTEMPTS:
                        if (correct / total) >= PracticeAttempt.MASTERY_THRESHOLD:
                            mastery_status = 'mastered'
                        elif (correct / total) >= PracticeAttempt.LEARNING_THRESHOLD:
                            mastery_status = 'learning'
                    
                    addition_stats[str(level)] = {
                        'description': description,
                        'attempts': total,
                        'accuracy': accuracy,
                        'avg_time': avg_time,
                        'mastery_status': mastery_status
                    }
            
            operation_stats['addition'] = {
                'total_attempts': total,
                'accuracy': accuracy,
                'current_streak': current_streak,
                'levels': addition_stats
            }
        
        # Get multiplication stats
        multiplication_attempts = PracticeAttempt.query.filter_by(
            user_id=student_id,
            operation='multiplication'
        ).all()
        
        if multiplication_attempts:
            total = len(multiplication_attempts)
            correct = len([a for a in multiplication_attempts if a.is_correct])
            accuracy = (correct / total * 100) if total > 0 else 0
            
            # Calculate current streak
            current_streak = 0
            for attempt in sorted(multiplication_attempts, key=lambda x: x.created_at, reverse=True):
                if attempt.is_correct:
                    current_streak += 1
                else:
                    break
            
            # Get level-specific stats
            multiplication_stats = {}
            for level, description in multiplication_levels.items():
                level_attempts = [a for a in multiplication_attempts if a.level == level]
                if level_attempts:
                    total = len(level_attempts)
                    correct = len([a for a in level_attempts if a.is_correct])
                    times = [a.time_taken for a in level_attempts if a.time_taken is not None]
                    avg_time = sum(times) / len(times) if times else 0
                    accuracy = (correct / total * 100) if total > 0 else 0
                    
                    # Determine mastery status
                    mastery_status = 'needs_practice'
                    if total >= PracticeAttempt.MIN_ATTEMPTS:
                        if (correct / total) >= PracticeAttempt.MASTERY_THRESHOLD:
                            mastery_status = 'mastered'
                        elif (correct / total) >= PracticeAttempt.LEARNING_THRESHOLD:
                            mastery_status = 'learning'
                    
                    multiplication_stats[str(level)] = {
                        'description': description,
                        'attempts': total,
                        'accuracy': accuracy,
                        'avg_time': avg_time,
                        'mastery_status': mastery_status
                    }
            
            operation_stats['multiplication'] = {
                'total_attempts': total,
                'accuracy': accuracy,
                'current_streak': current_streak,
                'levels': multiplication_stats
            }
        
        return render_template('progress.html',
                            stats=operation_stats,
                            student=student,
                            viewing_as_teacher=True)
                            
    except Exception as e:
        print(f"Error in student_progress route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading student progress data.', 'danger')
        return redirect(url_for('welcome'))

@app.route('/analyze_level/<operation>/<int:level>')
@app.route('/analyze_level/<operation>/<int:level>/<int:student_id>')
@login_required
def analyze_level(operation, level, student_id=None):
    try:
        # If student_id is provided and user is a teacher, show that student's progress
        if student_id:
            if not current_user.is_teacher:
                flash('Access denied. Teachers only.', 'danger')
                return redirect(url_for('welcome'))
            
            student = User.query.get_or_404(student_id)
            if student.teacher_id != current_user.id:
                flash('Access denied. Not your student.', 'danger')
                return redirect(url_for('welcome'))
            
            user_id = student_id
            viewing_as_teacher = True
        else:
            user_id = current_user.id
            student = current_user
            viewing_as_teacher = False

        # Get all attempts for this level
        attempts = PracticeAttempt.query.filter(
            PracticeAttempt.user_id == user_id,
            PracticeAttempt.operation == operation,
            PracticeAttempt.level == level
        ).order_by(PracticeAttempt.created_at.desc()).all()
        
        # Group attempts by problem
        problem_stats = {}
        for attempt in attempts:
            if attempt.problem not in problem_stats:
                problem_stats[attempt.problem] = {
                    'total_attempts': 0,
                    'correct_count': 0,
                    'incorrect_count': 0,
                    'user_answers': [],
                    'correct_answer': attempt.correct_answer,
                    'recent_attempts': []
                }
            
            stats = problem_stats[attempt.problem]
            stats['total_attempts'] += 1
            if attempt.is_correct:
                stats['correct_count'] += 1
            else:
                stats['incorrect_count'] += 1
                stats['user_answers'].append(attempt.user_answer)
            
            # Keep track of 5 most recent attempts
            stats['recent_attempts'].append({
                'is_correct': attempt.is_correct,
                'user_answer': attempt.user_answer,
                'time_taken': attempt.time_taken,
                'created_at': attempt.created_at
            })
            stats['recent_attempts'] = sorted(stats['recent_attempts'], 
                                           key=lambda x: x['created_at'], 
                                           reverse=True)[:5]
        
        # Convert to list and add mastery status
        problems_list = []
        for problem, stats in problem_stats.items():
            accuracy = (stats['correct_count'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
            
            # Determine mastery status
            mastery_status = 'needs_practice'
            if stats['total_attempts'] >= PracticeAttempt.MIN_ATTEMPTS:
                if accuracy >= PracticeAttempt.MASTERY_THRESHOLD * 100:
                    mastery_status = 'mastered'
                elif accuracy >= PracticeAttempt.LEARNING_THRESHOLD * 100:
                    mastery_status = 'learning'
            
            problems_list.append({
                'problem': problem,
                'total_attempts': stats['total_attempts'],
                'correct_count': stats['correct_count'],
                'incorrect_count': stats['incorrect_count'],
                'accuracy': accuracy,
                'user_answers': stats['user_answers'],
                'correct_answer': stats['correct_answer'],
                'mastery_status': mastery_status,
                'recent_attempts': stats['recent_attempts']
            })
        
        # Sort by mastery status (mastered first), then by accuracy
        problems_list.sort(key=lambda x: (
            0 if x['mastery_status'] == 'mastered' else
            1 if x['mastery_status'] == 'learning' else 2,
            -x['accuracy']
        ))
        
        # Calculate overall statistics
        total_attempts = len(attempts)
        correct_attempts = len([a for a in attempts if a.is_correct])
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        return render_template('analyze_level.html',
            operation=operation,
            level=level,
            total_attempts=total_attempts,
            correct_count=correct_attempts,
            incorrect_count=total_attempts - correct_attempts,
            accuracy=accuracy,
            problems=problems_list,
            student=student,
            viewing_as_teacher=viewing_as_teacher
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
