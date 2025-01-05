from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models.active_session import ActiveSession

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
    
    return render_template('active_students.html', active_sessions=active_sessions)