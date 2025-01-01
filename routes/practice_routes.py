from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models.practice_attempt import PracticeAttempt
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from utils.math_problems import get_problem, generate_custom_multiplication
from datetime import datetime

practice_bp = Blueprint('practice', __name__)

@practice_bp.route('/practice')
@login_required
def practice():
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
        return render_template('practice.html', 
                            mode='free')

@practice_bp.route('/get_problem', methods=['POST'])
@login_required
def get_problem_route():
    data = request.json
    assignment_id = data.get('assignment_id')
    
    if assignment_id:
        # Get problem based on assignment settings
        assignment = Assignment.query.get_or_404(assignment_id)
        problem = get_problem(
            operation=assignment.operation,
            level=assignment.level,
            custom_numbers=None if assignment.operation != 'multiplication' 
                        else [assignment.custom_number1, assignment.custom_number2]
        )
    else:
        # Free practice - use provided settings
        operation = data.get('operation', 'addition')
        level = int(data.get('level', 1))
        problem = get_problem(operation=operation, level=level)
    
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
        student_answer=answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        'correct': is_correct,
        'progress': {
            'attempted': getattr(progress, 'problems_attempted', 0),
            'correct': getattr(progress, 'problems_correct', 0),
            'completed': getattr(progress, 'completed', False)
        } if assignment_id else None
    })