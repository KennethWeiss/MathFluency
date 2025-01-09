from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models.practice_attempt import PracticeAttempt
from models.user import User
from models.class_ import Class, teacher_class
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from utils.math_problems import get_problem
from services.progress_service import ProgressService

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/progress')
@login_required
def progress():
    """Show user's progress across all operations"""
    try:
        # Get stats for each operation
        operations = ['addition', 'subtraction', 'multiplication', 'division']
        stats = {}
        
        for operation in operations:
            operation_stats = ProgressService.get_student_stats(current_user.id, operation)
            if operation_stats['total_attempts'] > 0:
                stats[operation] = operation_stats

        # Get multiplication table stats if available
        multiplication_stats = None
        if 'multiplication' in stats:
            multiplication_stats = ProgressService.get_multiplication_table_stats(current_user.id)

        return render_template('progress.html',
                            stats=stats,
                            multiplication_stats=multiplication_stats)
    except Exception as e:
        print(f"Error in progress route: {str(e)}")
        flash('An error occurred while loading progress data.', 'error')
        return redirect(url_for('main.index'))

@progress_bp.route('/student_progress/<int:student_id>')
@login_required
def student_progress(student_id):
    """View progress for a specific student (teacher only)"""
    try:
        if not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'error')
            return redirect(url_for('main.index'))

        student = User.query.get_or_404(student_id)
        
        # Check if teacher has access to this student
        teacher_classes = Class.query.join(teacher_class).filter_by(teacher_id=current_user.id).all()
        student_in_class = any(student in class_.students for class_ in teacher_classes)
        
        if not student_in_class:
            flash('Access denied. Student not in your classes.', 'error')
            return redirect(url_for('main.index'))

        # Get stats for each operation
        operations = ['addition', 'subtraction', 'multiplication', 'division']
        stats = {}
        
        for operation in operations:
            operation_stats = ProgressService.get_student_stats(student_id, operation)
            if operation_stats['total_attempts'] > 0:
                stats[operation] = operation_stats

        # Get multiplication table stats if available
        multiplication_stats = None
        if 'multiplication' in stats:
            multiplication_stats = ProgressService.get_multiplication_table_stats(student_id)

        return render_template('student_progress.html',
                            student=student,
                            stats=stats,
                            multiplication_stats=multiplication_stats)
    except Exception as e:
        print(f"Error in student_progress route: {str(e)}")
        flash('An error occurred while loading student progress data.', 'error')
        return redirect(url_for('main.index'))

@progress_bp.route('/analyze_level/<operation>/<int:level>')
@progress_bp.route('/analyze_level/<operation>/<int:level>/<int:student_id>')
@login_required
def analyze_level(operation, level, student_id=None):
    """Analyze performance at a specific level"""
    try:
        if student_id and not current_user.is_teacher:
            flash('Access denied. Teachers only.', 'error')
            return redirect(url_for('main.index'))

        target_id = student_id if student_id else current_user.id
        
        # Get attempts for this level
        attempts = PracticeAttempt.query.filter_by(
            user_id=target_id,
            operation=operation,
            level=level
        ).all()
        
        if not attempts:
            flash('No attempts found for this level.', 'warning')
            return redirect(url_for('progress.progress'))

        # Get problem description
        problem = get_problem(operation, level)
        description = problem['description'] if problem else f"Level {level}"

        # Calculate stats using ProgressService
        stats = ProgressService.calculate_level_stats(attempts, description)
        problems = ProgressService.analyze_level_problems(attempts)

        # Get student info if viewing as teacher
        student = User.query.get(target_id) if student_id else None

        return render_template('analyze_level.html',
                            operation=operation,
                            level=level,
                            stats=stats,
                            problems=problems,
                            student=student)
    except Exception as e:
        print(f"Error in analyze_level route: {str(e)}")
        flash('An error occurred while analyzing level data.', 'error')
        return redirect(url_for('progress.progress'))

@progress_bp.route('/incorrect_problems')
@login_required
def incorrect_problems():
    """Display problems the user has answered incorrectly"""
    try:
        missed_problems = ProgressService.analyze_missed_problems(current_user.id)
        return render_template('incorrect_problems.html', problems=missed_problems)
    except Exception as e:
        print(f"Error in incorrect_problems route: {str(e)}")
        flash('An error occurred while loading incorrect problems.', 'error')
        return redirect(url_for('progress.progress'))