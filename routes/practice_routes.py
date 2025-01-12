from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models.practice_attempt import PracticeAttempt
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from models.active_session import ActiveSession
from utils.math_problems import get_problem, generate_custom_multiplication
from datetime import datetime

practice_bp = Blueprint('practice', __name__)

@practice_bp.before_app_request
def update_session():
    if current_user.is_authenticated:
        session = ActiveSession.query.filter_by(user_id=current_user.id).first()
        if not session:
            session = ActiveSession(user_id=current_user.id)
            db.session.add(session)
        session.last_active = datetime.utcnow()
        db.session.commit()

@practice_bp.route('/practice')
@login_required
def practice():
    # Update session activity
    if current_user.is_authenticated:
        session = current_user.active_session
        if session:
            session.activity_type = 'practice'
            session.details = "Practice Mode"
            db.session.commit()

    # Get assignment_id from query params if it exists
    assignment_id = request.args.get('assignment_id')
    
    if assignment_id:
        # Assignment mode
        assignment = Assignment.query.get_or_404(assignment_id)
        progress = AssignmentProgress.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first_or_404()
        
        return render_template('practice.html', 
                            mode='assignment',
                            assignment=assignment,
                            progress=progress)
    else:
        # Free practice mode
        return render_template('practice.html', mode='practice')

@practice_bp.route('/get_problem', methods=['POST'])
@login_required
def get_problem_route():
    data = request.json
    assignment_id = data.get('assignment_id')
    
    if assignment_id:
        # Get problem based on assignment settings
        assignment = Assignment.query.get_or_404(assignment_id)
        if assignment.operation == 'multiplication' and assignment.custom_number1 and assignment.custom_number2:
            number1_spec = {'type': 'single', 'value': assignment.custom_number1}
            number2_spec = {'type': 'single', 'value': assignment.custom_number2}
            problem = generate_custom_multiplication(number1_spec, number2_spec)
        else:
            problem = get_problem(
                operation=assignment.operation,
                level=assignment.level
            )
    else:
        # Free practice - use provided settings
        operation = data.get('operation', 'addition')
        level = data.get('level', 1)
        
        if operation == 'multiplication' and level == 99:
            custom_numbers = data.get('customNumbers', {})
            number1_spec = {'type': 'single', 'value': custom_numbers.get('number1')}
            number2_spec = {'type': 'single', 'value': custom_numbers.get('number2')}
            problem = generate_custom_multiplication(number1_spec, number2_spec)
        else:
            problem = get_problem(operation=operation, level=level)
    
    if not problem:
        return jsonify({'error': 'Invalid operation or level'})
    
    return jsonify(problem)

@practice_bp.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    data = request.json
    answer = data.get('answer')
    correct_answer = data.get('correct_answer')
    time_taken = data.get('time_taken')
    assignment_id = data.get('assignment_id')
    
    is_correct = str(answer) == str(correct_answer)
    
    if assignment_id:
        # Record attempt for assignment
        assignment = Assignment.query.get_or_404(assignment_id)
        progress = AssignmentProgress.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first_or_404()
        
        # Update progress
        progress.problems_attempted += 1
        if is_correct:
            progress.problems_correct += 1
        
        # Check if assignment is complete
        if (progress.problems_attempted >= assignment.required_problems and
            (progress.problems_correct / progress.problems_attempted * 100) >= assignment.min_correct_percentage):
            progress.completed = True
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
    
    # Record attempt in practice history
    attempt = PracticeAttempt(
        user_id=current_user.id,
        operation=data.get('operation'),
        level=data.get('level'),
        problem=data.get('problem'),
        user_answer=answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Return progress info if this is an assignment
    if assignment_id:
        return jsonify({
            'is_correct': is_correct,
            'progress': {
                'problems_correct': progress.problems_correct,
                'required_problems': assignment.required_problems
            }
        })
    
    return jsonify({'is_correct': is_correct})