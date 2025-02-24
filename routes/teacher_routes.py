from flask import Blueprint, render_template, abort, Response, stream_with_context, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.active_session import ActiveSession
from models.practice_attempt import PracticeAttempt
from models.user import User
from models.class_ import Class
import json
import time



teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/active-students')
@login_required
def active_students():
    """View currently active students and their activities"""
    if not current_user.is_teacher:
        abort(403)  # Forbidden
        
    # Get sessions active in the last 15 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=ActiveSession.INACTIVE_THRESHOLD)
    active_sessions = ActiveSession.query.filter(
        ActiveSession.last_active >= cutoff
    ).order_by(ActiveSession.last_active.desc()).all()
    
    # Get performance data for each student
    student_stats = {}
    for session in active_sessions:
        # Get recent attempts (last 20) to calculate accuracy
        recent_attempts = PracticeAttempt.query.filter_by(
            user_id=session.user_id
        ).order_by(
            PracticeAttempt.created_at.desc()
        ).limit(20).all()
        
        if recent_attempts:
            correct = sum(1 for attempt in recent_attempts if attempt.is_correct)
            accuracy = (correct / len(recent_attempts)) * 100
            recent_operation = recent_attempts[0].operation if recent_attempts else None
        else:
            accuracy = 0 
            recent_operation = None
        
        student_stats[session.user_id] = {
            'accuracy': accuracy,
            'recent_attempts': recent_attempts,
            'accuracy_color': get_accuracy_color(accuracy),
            'recent_operation': recent_operation
        }
    
    return render_template('active_students.html', 
                        active_sessions=active_sessions,
                        student_stats=student_stats)

def get_accuracy_color(accuracy):
    """Return Bootstrap color class based on accuracy"""
    if accuracy >= 90:
        return 'success'
    elif accuracy >= 70:
        return 'warning'
    else:
        return 'danger'

def generate_student_updates():
    """Generate updates about active students"""
    while True:
        # Get active sessions
        cutoff = datetime.utcnow() - timedelta(minutes=ActiveSession.INACTIVE_THRESHOLD)
        active_sessions = ActiveSession.query.filter(
            ActiveSession.last_active >= cutoff
        ).order_by(ActiveSession.last_active.desc()).all()
        
        # Format data for SSE
        updates = []
        for session in active_sessions:
            updates.append({
                'user_id': session.user_id,
                'username': session.user.username,
                'last_active': session.last_active.isoformat(),
                'activity_type': session.activity_type,
                'details': session.details,
                'accuracy': get_student_accuracy(session.user_id)
            })
        
        # Send updates as SSE
        yield f"data: {json.dumps(updates)}\n\n"
        time.sleep(5)  # Wait 5 seconds before next update

def get_student_accuracy(user_id):
    """Get accuracy for a specific student"""
    recent_attempts = PracticeAttempt.query.filter_by(
        user_id=user_id
    ).order_by(
        PracticeAttempt.created_at.desc()
    ).limit(20).all()
    
    if recent_attempts:
        correct = sum(1 for attempt in recent_attempts if attempt.is_correct)
        return (correct / len(recent_attempts)) * 100
    return 0

@teacher_bp.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    """Edit a student's information"""
    if not current_user.is_teacher:
        abort(403)
        
    student = User.query.get_or_404(student_id)
    
    # Ensure the student is in one of the teacher's classes
    if not any(c in current_user.teaching_classes for c in student.enrolled_classes):
        abort(403)
        
    if request.method == 'POST':
        student.first_name = request.form.get('first_name', student.first_name)
        student.last_name = request.form.get('last_name', student.last_name)
        student.email = request.form.get('email', student.email)
        db.session.commit()
        flash('Student information updated successfully', 'success')
        return redirect(url_for('teacher.active_students'))
    
    return render_template('teacher/edit_student.html', student=student)

@teacher_bp.route('/create-student/<int:class_id>', methods=['GET', 'POST'])
@login_required
def create_student(class_id):
    """Create a new student and optionally add them to a class"""
    if not current_user.is_teacher:
        abort(403)  # Forbidden
    
    # Get the class if class_id is provided
    class_ = Class.query.get_or_404(class_id)
    
    # Check if teacher has access to this class
    if current_user not in class_.teachers:
        abort(403)  # Forbidden
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not first_name or not last_name or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('teacher/create_student.html', class_=class_)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('teacher/create_student.html', class_=class_)
        
        # Create username from first and last name
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        username = base_username
        counter = 1
        
        # Keep trying usernames until we find an unused one
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create the new student
        student = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email if email else None,
            is_teacher=False
        )
        student.set_password(password)
        
        db.session.add(student)
        
        # Add student to the class
        class_.add_student(student)
        
        db.session.commit()
        
        flash(f'Student {username} created and added to class successfully!', 'success')
        return redirect(url_for('class.manage_students', id=class_id))
    
    return render_template('teacher/create_student.html', class_=class_)

@teacher_bp.route('/active-students/updates')
@login_required
def active_students_updates():
    """SSE endpoint for active student updates"""
    if not current_user.is_teacher:
        abort(403)
    return Response(
        stream_with_context(generate_student_updates()),
        mimetype='text/event-stream'
    )
