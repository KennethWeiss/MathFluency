from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models.practice_attempt import PracticeAttempt
from models.user import User
from models.class_ import Class, teacher_class
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from utils.math_problems import get_problem

progress_bp = Blueprint('progress', __name__)

def calculate_level_stats(attempts, description):
    """Calculate stats for a specific level"""
    total = len(attempts)
    correct = len([a for a in attempts if a.is_correct])
    times = [a.time_taken for a in attempts if a.time_taken is not None]
    avg_time = sum(times) / len(times) if times else 0
    accuracy = (correct / total * 100) if total > 0 else 0
    
    mastery_status = 'needs_practice'
    if total >= PracticeAttempt.MIN_ATTEMPTS:  # At least 3 attempts
        accuracy_ratio = correct / total
        if accuracy_ratio >= PracticeAttempt.MASTERY_THRESHOLD:  # 80% or higher
            mastery_status = 'mastered'
        elif accuracy_ratio >= PracticeAttempt.LEARNING_THRESHOLD:  # 60% or higher
            mastery_status = 'learning'
    
    return {
        'description': description,
        'attempts': total,
        'correct': correct,
        'accuracy': accuracy,
        'avg_time': avg_time,
        'mastery_status': mastery_status
    }

def get_operation_stats(user_id, operation):
    """Get stats for a specific operation"""
    # Get attempts
    attempts = PracticeAttempt.query.filter_by(
        user_id=user_id,
        operation=operation
    ).all()
    
    if not attempts:
        return None
    
    # Basic stats    
    total = len(attempts)
    correct = len([a for a in attempts if a.is_correct])
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Get level stats
    levels_stats = {}
    for level in sorted(set(a.level for a in attempts)):
        # Get a problem to get its description
        problem = get_problem(operation, level)
        if problem:
            level_attempts = [a for a in attempts if a.level == level]
            levels_stats[str(level)] = calculate_level_stats(
                level_attempts, 
                problem['description']
            )
    
    return {
        'total_attempts': total,
        'accuracy': accuracy,
        'levels': levels_stats
    }

def analyze_missed_problems(user_id, operation=None):
    """Analyze commonly missed problems for a user"""
    # Get attempts
    query = PracticeAttempt.query.filter_by(user_id=user_id, is_correct=False)
    if operation:
        query = query.filter_by(operation=operation)
    missed_attempts = query.all()
    
    problem_stats = {}
    
    for attempt in missed_attempts:
        if attempt.problem not in problem_stats:
            problem_stats[attempt.problem] = {
                'total_attempts': 1,
                'incorrect_attempts': 1,
                'last_seen': attempt.created_at,
                'operation': attempt.operation,
                'level': attempt.level
            }
    
    return problem_stats

def get_problem_history(user_id, operation=None, limit=10):
    """Get recent problem history for a user, optionally filtered by operation."""
    query = PracticeAttempt.query.filter_by(user_id=user_id)
    if operation:
        query = query.filter_by(operation=operation)
    return query.order_by(PracticeAttempt.created_at.desc()).limit(limit).all()

def analyze_level_problems(attempts):
    """Analyze all problems for a specific level."""
    problem_stats = {}
    
    for attempt in attempts:
        if attempt.problem not in problem_stats:
            problem_stats[attempt.problem] = {
                'total_attempts': 0,
                'correct_count': 0,
                'last_seen': attempt.created_at,
                'operation': attempt.operation,
                'level': attempt.level,
                'user_answers': [],
                'correct_answer': attempt.correct_answer,
                'consecutive_wrong': 0,
                'needs_practice': False
            }
        
        stats = problem_stats[attempt.problem]
        stats['total_attempts'] += 1
        if attempt.is_correct:
            stats['correct_count'] += 1
        else:
            stats['user_answers'].append(attempt.user_answer)
        
        # Update last seen if more recent
        if attempt.created_at > stats['last_seen']:
            stats['last_seen'] = attempt.created_at
    
    # Convert to list and add accuracy
    problem_list = []
    for problem, stats in problem_stats.items():
        accuracy = (stats['correct_count'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
        problem_list.append({
            'problem': problem,
            'total_attempts': stats['total_attempts'],
            'correct_count': stats['correct_count'],
            'incorrect_count': stats['total_attempts'] - stats['correct_count'],
            'accuracy': accuracy,
            'last_seen': stats['last_seen'],
            'operation': stats['operation'],
            'level': stats['level'],
            'user_answers': list(set(stats['user_answers'])),  # Remove duplicates
            'correct_answer': stats['correct_answer'],
            'consecutive_wrong': stats['consecutive_wrong'],
            'needs_practice': stats['needs_practice']
        })
    
    # Sort by accuracy (ascending) and then by consecutive wrong attempts (descending)
    return sorted(
        problem_list, 
        key=lambda x: (x['accuracy'], -x['consecutive_wrong'])
    )

def get_multiplication_table_stats(user_id):
    """Get stats for each multiplication problem (0-12 × 0-12)"""
    # Get all multiplication attempts
    attempts = PracticeAttempt.query.filter_by(
        user_id=user_id,
        operation='multiplication'
    ).all()
    
    # Initialize stats dictionary
    stats = {}
    for i in range(13):
        stats[i] = {}
        for j in range(13):
            stats[i][j] = {'attempts': 0, 'correct': 0, 'accuracy': 0}
    
    # Calculate stats for each problem
    for attempt in attempts:
        # Extract numbers from problem string (e.g., "5 × 8")
        nums = [int(n) for n in attempt.problem.split('×')]
        if len(nums) == 2:
            n1, n2 = nums
            if n1 <= 12 and n2 <= 12:
                # Store stats in both positions (n1,n2) and (n2,n1)
                for i, j in [(n1, n2), (n2, n1)]:
                    stats[i][j]['attempts'] += 1
                    if attempt.is_correct:
                        stats[i][j]['correct'] += 1
    
    # Calculate accuracy percentages
    for i in range(13):
        for j in range(13):
            attempts = stats[i][j]['attempts']
            if attempts > 0:
                stats[i][j]['accuracy'] = (stats[i][j]['correct'] / attempts) * 100
    
    return stats

@progress_bp.route('/progress')
@login_required
def progress():
    """Show user progress"""
    try:
        # If viewing as teacher with student_id parameter, redirect to student_progress
        student_id = request.args.get('student_id')
        if student_id:
            if not current_user.is_teacher:
                flash('Access denied. Teachers only.', 'danger')
                return redirect(url_for('main.welcome'))
            return redirect(url_for('progress.student_progress', student_id=student_id))
        
        # Get stats for each operation
        stats = {}
        for operation in ['addition', 'multiplication']:  # Add more operations here
            operation_stats = get_operation_stats(current_user.id, operation)
            if operation_stats:
                stats[operation] = operation_stats
        
        # Get multiplication table stats
        mult_table_stats = get_multiplication_table_stats(current_user.id)
        
        return render_template('progress.html',
                            stats=stats,
                            mult_table_stats=mult_table_stats,
                            viewing_as_teacher=False)
        
    except Exception as e:
        print(f"Error in progress route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading progress data.', 'danger')
        return redirect(url_for('main.welcome'))

@progress_bp.route('/student_progress/<int:student_id>')
@login_required
def student_progress(student_id):
    """View progress for a specific student (teacher only)"""
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.welcome'))
    
    # Get student
    student = User.query.get(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('progress.progress'))
        
    # Check if student is in any of teacher's classes
    teacher_classes = current_user.teaching_classes.all()
    student_in_class = False
    for class_ in teacher_classes:
        if student in class_.students:
            student_in_class = True
            break
    
    if not student_in_class:
        flash('Access denied. Not your student.', 'danger')
        return redirect(url_for('progress.progress'))
    
    # Get stats for each operation
    stats = {}
    for operation in ['addition', 'multiplication']:
        operation_stats = get_operation_stats(student_id, operation)
        if operation_stats:
            stats[operation] = operation_stats
    
    # Get multiplication table stats
    mult_table_stats = get_multiplication_table_stats(student_id)
    
    return render_template('progress.html',
                        stats=stats,
                        student=student,
                        mult_table_stats=mult_table_stats,
                        viewing_as_teacher=True)

@progress_bp.route('/analyze_level/<operation>/<int:level>')
@progress_bp.route('/analyze_level/<operation>/<int:level>/<int:student_id>')
@login_required
def analyze_level(operation, level, student_id=None):
    """Analyze performance at a specific level"""
    try:
        if student_id and not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('main.welcome'))
        
        user_id = student_id if student_id else current_user.id
        
        # Get the student if viewing as teacher
        student = None
        if student_id:
            student = User.query.get(student_id)
            if not student:
                flash('Student not found.', 'danger')
                return redirect(url_for('progress.progress'))
        
        # Get attempts for this level
        attempts = PracticeAttempt.query.filter_by(
            user_id=user_id,
            operation=operation,
            level=level
        ).order_by(PracticeAttempt.created_at.desc()).all()
        
        if not attempts:
            flash('No attempts found for this level.', 'warning')
            return redirect(url_for('progress.progress'))
        
        # Get level description from math_problems
        problem = get_problem(operation, level)
        if not problem:
            flash('Invalid operation or level.', 'danger')
            return redirect(url_for('progress.progress'))
            
        description = problem['description']
        
        # Calculate stats using our helper
        stats = calculate_level_stats(attempts, description)
        
        # Get recent attempts
        recent_attempts = attempts[:10]  # Last 10 attempts
        
        # Calculate correct and incorrect counts
        total_attempts = stats['attempts']
        correct_count = stats['correct']
        incorrect_count = total_attempts - correct_count
        accuracy = stats['accuracy']
        
        # Analyze problems
        problems = analyze_level_problems(attempts)
        
        return render_template('analyze_level.html',
                            operation=operation,
                            level=level,
                            description=description,
                            stats=stats,
                            recent_attempts=recent_attempts,
                            total_attempts=total_attempts,
                            correct_count=correct_count,
                            incorrect_count=incorrect_count,
                            accuracy=accuracy,
                            problems=problems,
                            student=student)  # Pass the student object
    
    except Exception as e:
        print(f"Error in analyze_level route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while analyzing level data.', 'danger')
        return redirect(url_for('progress.progress'))

@progress_bp.route('/incorrect_problems')
@login_required
def incorrect_problems():
    """Display problems the user has answered incorrectly"""
    try:
        # Get missed problems
        problems = analyze_missed_problems(current_user.id)
        
        return render_template('incorrect_problems.html', 
                            problems=problems)
    except Exception as e:
        print(f"Error in incorrect_problems route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading incorrect problems.', 'danger')
        return redirect(url_for('progress.progress'))