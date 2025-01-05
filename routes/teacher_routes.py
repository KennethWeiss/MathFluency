from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models.active_session import ActiveSession
from models.practice_attempt import PracticeAttempt
from sqlalchemy import func

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
            operation_counts = {}
            for attempt in recent_attempts:
                operation_counts[attempt.operation] = operation_counts.get(attempt.operation, 0) + 1
            most_practiced = max(operation_counts.items(), key=lambda x: x[1])[0] if operation_counts else None
        else:
            accuracy = 0
            most_practiced = None
            
        student_stats[session.user_id] = {
            'accuracy': accuracy,
            'most_practiced': most_practiced,
            'accuracy_color': get_accuracy_color(accuracy)
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