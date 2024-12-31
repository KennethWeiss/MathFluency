from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models.practice_attempt import PracticeAttempt
from models.user import User
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

progress_bp = Blueprint('progress', __name__)

# Constants
ADDITION_LEVELS = {
    1: "Adding 1 to single digit",
    2: "Adding 2 to single digit",
    3: "Make 10",
    4: "Add single digit to double digit",
    5: "Add double digit to double digit"
}

MULTIPLICATION_LEVELS = {i: f"× {i} Table" for i in range(13)}  # 0-12 tables

def calculate_streak(attempts):
    """Calculate current streak from attempts"""
    streak = 0
    for attempt in sorted(attempts, key=lambda x: x.created_at, reverse=True):
        if attempt.is_correct:
            streak += 1
        else:
            break
    return streak

def calculate_level_stats(attempts, description):
    """Calculate stats for a specific level"""
    total = len(attempts)
    correct = len([a for a in attempts if a.is_correct])
    times = [a.time_taken for a in attempts if a.time_taken is not None]
    avg_time = sum(times) / len(times) if times else 0
    accuracy = (correct / total * 100) if total > 0 else 0
    
    mastery_status = 'needs_practice'
    if total >= PracticeAttempt.MIN_ATTEMPTS:
        if (correct / total) >= PracticeAttempt.MASTERY_THRESHOLD:
            mastery_status = 'mastered'
        elif (correct / total) >= PracticeAttempt.LEARNING_THRESHOLD:
            mastery_status = 'learning'
    
    return {
        'description': description,
        'attempts': total,
        'accuracy': accuracy,
        'avg_time': avg_time,
        'mastery_status': mastery_status
    }

def get_level_stats(attempts, level_descriptions):
    """Get stats for each level of an operation"""
    stats = {}
    for level, description in level_descriptions.items():
        level_attempts = [a for a in attempts if a.level == level]
        if level_attempts:
            stats[str(level)] = calculate_level_stats(level_attempts, description)
    return stats

def get_operation_stats(user_id, operation, levels):
    """Get stats for a specific operation (addition/multiplication)"""
    attempts = PracticeAttempt.query.filter_by(
        user_id=user_id,
        operation=operation
    ).all()
    
    if not attempts:
        return None
        
    total = len(attempts)
    correct = len([a for a in attempts if a.is_correct])
    accuracy = (correct / total * 100) if total > 0 else 0
    current_streak = calculate_streak(attempts)
    
    return {
        'total_attempts': total,
        'accuracy': accuracy,
        'current_streak': current_streak,
        'levels': get_level_stats(attempts, levels)
    }

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
                'level': attempt.level
            }
        
        problem_stats[attempt.problem]['total_attempts'] += 1
        if attempt.is_correct:
            problem_stats[attempt.problem]['correct_count'] += 1
        
        # Update last seen if this attempt is more recent
        if attempt.created_at > problem_stats[attempt.problem]['last_seen']:
            problem_stats[attempt.problem]['last_seen'] = attempt.created_at
    
    # Convert to list and add accuracy
    problem_list = []
    for problem, stats in problem_stats.items():
        accuracy = (stats['correct_count'] / stats['total_attempts'] * 100) if stats['total_attempts'] > 0 else 0
        incorrect_count = stats['total_attempts'] - stats['correct_count']
        problem_list.append({
            'problem': problem,
            'total_attempts': stats['total_attempts'],
            'correct_count': stats['correct_count'],
            'incorrect_count': incorrect_count,
            'accuracy': accuracy,
            'last_seen': stats['last_seen'],
            'operation': stats['operation'],
            'level': stats['level']
        })
    
    # Sort by accuracy (ascending) so struggles are first
    return sorted(problem_list, key=lambda x: x['accuracy'])

@progress_bp.route('/progress')
@login_required
def progress():
    try:
        # If viewing as teacher with student_id parameter, redirect to student_progress
        student_id = request.args.get('student_id')
        if current_user.is_teacher and student_id:
            return redirect(url_for('progress.student_progress', student_id=student_id))
            
        operation_stats = {}
        for op, levels in [('addition', ADDITION_LEVELS), ('multiplication', MULTIPLICATION_LEVELS)]:
            stats = get_operation_stats(current_user.id, op, levels)
            if stats:
                operation_stats[op] = stats
        
        return render_template('progress.html', 
                            stats=operation_stats,
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
    try:
        # Verify current user is a teacher
        if not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'danger')
            return redirect(url_for('main.welcome'))
        
        # Get the student
        student = User.query.get_or_404(student_id)
        
        # Verify student belongs to this teacher
        if student.teacher_id != current_user.id:
            flash('Access denied. Not your student.', 'danger')
            return redirect(url_for('main.welcome'))
        
        # Get operation-specific stats
        operation_stats = {}
        for op, levels in [('addition', ADDITION_LEVELS), ('multiplication', MULTIPLICATION_LEVELS)]:
            stats = get_operation_stats(student_id, op, levels)
            if stats:
                operation_stats[op] = stats
        
        return render_template('progress.html',
                            stats=operation_stats,
                            student=student,
                            viewing_as_teacher=True)
    except Exception as e:
        print(f"Error in student_progress route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading student progress data.', 'danger')
        return redirect(url_for('main.welcome'))

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
        
        # Get attempts for this level
        attempts = PracticeAttempt.query.filter_by(
            user_id=user_id,
            operation=operation,
            level=level
        ).order_by(PracticeAttempt.created_at.desc()).all()
        
        if not attempts:
            flash('No attempts found for this level.', 'warning')
            return redirect(url_for('progress.progress'))
        
        # Get level description
        levels = ADDITION_LEVELS if operation == 'addition' else MULTIPLICATION_LEVELS
        description = levels.get(level, f"Level {level}")
        
        # Calculate stats using our helper
        stats = calculate_level_stats(attempts, description)
        
        # Get recent attempts
        recent_attempts = attempts[:10]  # Last 10 attempts
        
        # Calculate correct and incorrect counts
        total_attempts = stats['attempts']
        correct_count = int(total_attempts * stats['accuracy'] / 100)
        incorrect_count = total_attempts - correct_count
        
        # Analyze all problems at this level
        problems = analyze_level_problems(attempts)
        
        return render_template('analyze_level.html',
                            operation=operation,
                            level=level,
                            stats=stats,
                            recent_attempts=recent_attempts,
                            accuracy=stats['accuracy'],
                            correct_count=correct_count,
                            incorrect_count=incorrect_count,
                            problems=problems)

    except Exception as e:
        print(f"Error in analyze_level route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while analyzing level data.', 'danger')
        return redirect(url_for('main.welcome'))


@progress_bp.route('/incorrect_problems')
@login_required
def incorrect_problems():
    """Display problems the user has answered incorrectly"""
    try:
        # Get incorrect attempts grouped by problem
        missed_problems = analyze_missed_problems(current_user.id)
        
        return render_template('incorrect_problems.html',
                            problems=missed_problems)  # Already sorted by incorrect_attempts
    except Exception as e:
        print(f"Error in incorrect_problems route: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('An error occurred while loading incorrect problems.', 'danger')
        return redirect(url_for('main.welcome'))