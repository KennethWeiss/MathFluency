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

@practice_bp.route('/progress')
@login_required
def progress():
    """Show student's practice progress"""
    # Get all practice attempts for the current user
    attempts = PracticeAttempt.query.filter_by(user_id=current_user.id).order_by(PracticeAttempt.created_at.desc()).all()
    
    # Calculate statistics by operation
    stats = {}
    operations = ['addition', 'multiplication']  # Support for these operations initially
    
    for op in operations:
        op_attempts = [a for a in attempts if a.operation == op]
        if op_attempts:
            total_attempts = len(op_attempts)
            correct_attempts = sum(1 for a in op_attempts if a.is_correct)
            
            # Calculate current streak
            current_streak = 0
            for attempt in op_attempts:
                if attempt.is_correct:
                    current_streak += 1
                else:
                    break
            
            stats[op] = {
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'accuracy': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'average_time': sum(a.time_taken for a in op_attempts) / total_attempts if total_attempts > 0 else 0,
                'current_streak': current_streak,
                'levels': {}  # For tracking progress at different levels
            }
            
            # Calculate stats by level
            for attempt in op_attempts:
                level = attempt.level
                if level not in stats[op]['levels']:
                    level_attempts = [a for a in op_attempts if a.level == level]
                    level_correct = sum(1 for a in level_attempts if a.is_correct)
                    
                    stats[op]['levels'][level] = {
                        'attempts': len(level_attempts),
                        'correct': level_correct,
                        'accuracy': (level_correct / len(level_attempts) * 100) if level_attempts else 0,
                        'total_time': sum(a.time_taken for a in level_attempts),
                        'description': get_level_description(op, level),
                        'mastery_status': PracticeAttempt.get_mastery_status(db.session, current_user.id, op, level)
                    }
    
    # Calculate multiplication table stats if available
    mult_table_stats = None
    if 'multiplication' in stats:
        mult_attempts = [a for a in attempts if a.operation == 'multiplication']
        mult_table_stats = {}
        for i in range(13):
            mult_table_stats[i] = {}
            for j in range(13):
                mult_table_stats[i][j] = {
                    'attempts': 0,
                    'correct': 0,
                    'accuracy': 0,
                    'average_time': 0
                }
        
        for i in range(1, 13):  # 1-12 multiplication tables
            for j in range(1, 13):
                problem = f"{i} × {j}"
                relevant_attempts = [a for a in mult_attempts if a.problem == problem]
                if relevant_attempts:
                    correct_count = sum(1 for a in relevant_attempts if a.is_correct)
                    mult_table_stats[i][j] = {
                        'attempts': len(relevant_attempts),
                        'correct': correct_count,
                        'accuracy': (correct_count / len(relevant_attempts)) * 100,
                        'average_time': sum(a.time_taken for a in relevant_attempts) / len(relevant_attempts)
                    }
    
    return render_template('progress.html',
                         stats=stats,
                         mult_table_stats=mult_table_stats,
                         viewing_as_teacher=False,
                         student=current_user)

def get_level_description(operation, level):
    """Get a description for each level of an operation"""
    if operation == 'addition':
        descriptions = {
            1: "Single Digit",
            2: "Double Digit",
            3: "Make 10",
            4: "Add to 100",
            5: "Add to 1000"
        }
    elif operation == 'multiplication':
        descriptions = {
            1: "×1 Table",
            2: "×2 Table",
            3: "×3 Table",
            4: "×4 Table",
            5: "×5 Table",
            6: "×6 Table",
            7: "×7 Table",
            8: "×8 Table",
            9: "×9 Table",
            10: "×10 Table",
            11: "×11 Table",
            12: "×12 Table"
        }
    else:
        return f"Level {level}"
    
    return descriptions.get(level, f"Level {level}")