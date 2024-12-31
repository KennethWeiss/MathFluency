from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models.practice_attempt import PracticeAttempt
from models.user import User
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

progress_bp = Blueprint('progress', __name__)


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


@progress_bp.route('/progress')
@login_required
def progress():
    try:
        # If viewing as teacher with student_id parameter, redirect to student_progress
        student_id = request.args.get('student_id')
        if current_user.is_teacher and student_id:
            return redirect(url_for('progress.student_progress', student_id=student_id))
            
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
        return redirect(url_for('main.welcome'))


@progress_bp.route('/analyze_level/<operation>/<int:level>')
@progress_bp.route('/analyze_level/<operation>/<int:level>/<int:student_id>')
@login_required
def analyze_level(operation, level, student_id=None):
    try:
        # If student_id is provided and user is a teacher, show that student's progress
        if student_id:
            if not current_user.is_teacher:
                flash('Access denied. Teachers only.', 'danger')
                return redirect(url_for('main.welcome'))
            
            student = User.query.get_or_404(student_id)
            if student.teacher_id != current_user.id:
                flash('Access denied. Not your student.', 'danger')
                return redirect(url_for('main.welcome'))
            
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


@progress_bp.route('/incorrect_problems')
@login_required
def incorrect_problems():
    # Get incorrect attempts for the current user
    incorrect_attempts = PracticeAttempt.query.filter_by(
        user_id=current_user.id,
        is_correct=False
    ).order_by(PracticeAttempt.created_at.desc()).all()
    
    return render_template('incorrect_problems.html', attempts=incorrect_attempts)
