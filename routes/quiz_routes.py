from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.quiz import Quiz, QuizParticipant
from models.user import User
from app import db
from sqlalchemy import and_

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/')
@login_required
def index():
    if current_user.is_teacher:
        return redirect(url_for('quiz.teacher_quizzes'))
    else:
        return redirect(url_for('quiz.student_quizzes'))

@quiz_bp.route('/student')
@login_required
def student_quizzes():
    # Get active quizzes where the student is a participant
    active_quizzes = Quiz.query\
        .join(QuizParticipant)\
        .filter(
            and_(
                QuizParticipant.user_id == current_user.id,
                Quiz.status.in_(['waiting', 'active'])
            )
        )\
        .all()
    
    return render_template('quiz/student_quizzes.html', quizzes=active_quizzes)

@quiz_bp.route('/teacher')
@login_required
def teacher_quizzes():
    if not current_user.is_teacher and not current_user.is_admin:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.home'))
    
    quizzes = Quiz.query.filter_by(teacher_id=current_user.id).order_by(Quiz.created_at.desc()).all()
    return render_template('quiz/teacher_quizzes.html', quizzes=quizzes)

@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if not current_user.is_teacher and not current_user.is_admin:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        operation = request.form.get('operation')
        duration = request.form.get('duration', type=int)
        adaptive = request.form.get('adaptive') == 'on'
        
        if not all([title, operation, duration]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('quiz.create_quiz'))
        
        quiz = Quiz(
            title=title,
            teacher_id=current_user.id,
            operation=operation,
            duration=duration,
            adaptive=adaptive,
            status='waiting'
        )
        db.session.add(quiz)
        db.session.commit()
        
        return redirect(url_for('quiz.teacher_panel', quiz_id=quiz.id))
    
    return render_template('quiz/create.html')

@quiz_bp.route('/teacher/<int:quiz_id>')
@login_required
def teacher_panel(quiz_id):
    if not current_user.is_teacher and not current_user.is_admin:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.home'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.id:
        flash('Access denied. Not your quiz.', 'danger')
        return redirect(url_for('quiz.teacher_quizzes'))
    
    # Get participants with their user information
    participants = QuizParticipant.query\
        .filter_by(quiz_id=quiz_id)\
        .join(QuizParticipant.user)\
        .all()
        
    return render_template('quiz/teacher_panel.html', quiz=quiz, participants=participants)

@quiz_bp.route('/<int:quiz_id>/join')
@login_required
def join_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is joinable
    if quiz.status == 'finished':
        flash('This quiz has already ended.', 'warning')
        return redirect(url_for('quiz.student_quizzes'))
    
    # Check if already a participant
    participant = QuizParticipant.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        participant = QuizParticipant(
            quiz_id=quiz_id,
            user_id=current_user.id,
            score=0
        )
        db.session.add(participant)
        db.session.commit()
    
    return render_template('quiz/play.html', quiz=quiz)

# API endpoints for WebSocket updates
@quiz_bp.route('/<int:quiz_id>/status', methods=['POST'])
@login_required
def update_quiz_status(quiz_id):
    if not current_user.is_teacher and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.id:
        return jsonify({'error': 'Not your quiz'}), 403
    
    status = request.json.get('status')
    if status in ['waiting', 'active', 'paused', 'completed']:
        quiz.status = status
        db.session.commit()
        return jsonify({'status': status})
    
    return jsonify({'error': 'Invalid status'}), 400

@quiz_bp.route('/<int:quiz_id>/leaderboard')
@login_required
def get_leaderboard(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    participants = QuizParticipant.query.filter_by(quiz_id=quiz_id)\
        .join(User)\
        .order_by(QuizParticipant.score.desc())\
        .all()
    
    leaderboard = [{
        'name': p.user.username,
        'score': p.score,
        'id': p.user.id
    } for p in participants]
    
    return jsonify(leaderboard)
