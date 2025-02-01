from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models.practice_attempt import PracticeAttempt
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from models.active_session import ActiveSession
from utils.math_problems import get_problem, generate_custom_multiplication
from services.progress_service import ProgressService
from datetime import datetime
from utils.practice_tracker import PracticeTracker

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
    print("Get problem route")
    print(f"Received data: {request.get_json()}")
    data = request.get_json()
    operation = data.get('operation')
    level = data.get('level', 1)
    assignment_id = data.get('assignment_id')

    # Validate operation and level
    if not operation or not isinstance(level, (int, str)):
        return jsonify({'error': 'Invalid operation or level'})
    try:
        level = int(level)
    except ValueError:
        return jsonify({'error': 'Invalid level format'})

    # If in assignment mode, validate and get settings
    if assignment_id:
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Invalid assignment'})

        # Get progress to check if assignment is complete
        progress = AssignmentProgress.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()

        if not progress:
            return jsonify({'error': 'No progress record found'})

        if progress.status == 'complete':
            return jsonify({
                'complete': True,
                'message': 'Assignment complete!'
            })

        # Use assignment settings
        operation = assignment.operation
        level = assignment.level

    # Get problem using PracticeTracker
    try:
        problem = PracticeTracker.get_problem(
            db=db,
            operation=operation,
            level=level,
            user_id=current_user.id
        )
        
        if not problem:
            return jsonify({
                'error': 'No problems available',
                'message': 'No problems found for this operation and level'
            }), 404

    except Exception as e:
        print(f"Error getting problem: {str(e)}")
        return jsonify({
            'error': 'Problem generation failed',
            'message': str(e)
        }), 500
    
    # Check if this is a level up response
    if problem.get('level_up'):
        return jsonify({
            'level_up': True,
            'new_level': problem['new_level'],
            'message': f'Congratulations! You have mastered level {level}!\n'
                      f'Accuracy: {problem["accuracy"]:.1f}%\n'
                      f'Average Time: {problem["avg_time"]:.1f}s'
        })
    
    return jsonify(problem)

@practice_bp.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug print
        
        # Extract and validate data
        operation = data.get('operation')
        try:
            level = int(data.get('level', 1))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid level format'}), 400
            
        problem = data.get('problem')
        try:
            user_answer = int(data.get('answer', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid answer format'}), 400
            
        time_taken = data.get('time_taken')
        assignment_id = data.get('assignment_id')
        
        # Validate required fields
        if not all([operation, problem]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get correct answer from problem
        try:
            if operation == 'multiplication':
                problem_parts = problem.split('×')
            else:
                problem_parts = problem.split(OPERATIONS[operation]['symbol'])
                
            num1 = int(problem_parts[0].strip())
            num2 = int(problem_parts[1].strip())
            
            if operation == 'addition':
                correct_answer = num1 + num2
            elif operation == 'subtraction':
                correct_answer = num1 - num2
            elif operation == 'multiplication':
                correct_answer = num1 * num2
            elif operation == 'division':
                correct_answer = num1 / num2
            else:
                return jsonify({'error': 'Invalid operation'}), 400
                
        except (IndexError, ValueError) as e:
            print(f"Error parsing problem: {e}")  # Debug print
            return jsonify({'error': 'Invalid problem format'}), 400
        
        is_correct = (user_answer == correct_answer)
        
        # Create attempt record
        attempt = PracticeAttempt(
            user_id=current_user.id,
            operation=operation,
            level=level,
            problem=problem,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            time_taken=time_taken
        )
        db.session.add(attempt)
        
        # For multiplication, add a second attempt record for the commutative case
        if operation == 'multiplication':
            num1, num2 = map(int, problem.split('×'))
            if num1 != num2:  # Only if numbers are different
                # Create commutative attempt with swapped numbers
                commutative_problem = f"{num2} × {num1}"
                commutative_attempt = PracticeAttempt(
                    user_id=current_user.id,
                    operation=operation,
                    level=max(num1, num2),  # Use larger number as level
                    problem=commutative_problem,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    time_taken=time_taken
                )
                db.session.add(commutative_attempt)
                print(f"Added commutative attempt: {commutative_problem} at level {max(num1, num2)}")  # Debug log
        
        # Update assignment progress if in assignment mode
        progress = None
        if assignment_id:
            progress = AssignmentProgress.query.filter_by(
                assignment_id=assignment_id,
                student_id=current_user.id
            ).first()
            
            if progress:
                progress.total_attempts += 1
                if attempt.is_correct:
                    progress.correct_answers += 1
                    progress.problems_completed += 1
                
                # Add to attempt history
                history = AttemptHistory(
                    progress_id=progress.id,
                    problem_number=progress.problems_completed,
                    student_answer=str(attempt.user_answer),
                    correct_answer=str(attempt.correct_answer),
                    is_correct=attempt.is_correct,
                    attempt_number=progress.total_attempts,
                    created_at=datetime.utcnow()
                )
                db.session.add(history)
                
                # Check if assignment is complete
                assignment = Assignment.query.get(assignment_id)
                if progress.correct_answers >= assignment.required_problems:
                    progress.status = 'complete'
                    progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Check if level should change
        should_change, new_level = ProgressService.should_change_level(
            current_user.id, operation, level
        )
        
        response_data = {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'should_change_level': should_change,
            'new_level': new_level if should_change else level
        }
        
        # Add progress info if in assignment mode
        if assignment_id and progress:
            response_data['progress'] = {
                'correct_answers': progress.correct_answers,
                'total_attempts': progress.total_attempts,
                'problems_completed': progress.problems_completed,
                'required_problems': progress.assignment.required_problems,
                'status': progress.status
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in check_answer: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

# Operation symbols for parsing problems
OPERATIONS = {
    'addition': {'symbol': '+'},
    'subtraction': {'symbol': '-'},
    'multiplication': {'symbol': '×'},
    'division': {'symbol': '÷'}
}

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
                'average_time': sum(a.time_taken for a in op_attempts if a.time_taken is not None) / sum(1 for a in op_attempts if a.time_taken is not None) if total_attempts > 0 else 0,
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
                        'total_time': sum(a.time_taken for a in level_attempts if a.time_taken is not None),
                        'description': get_level_description(op, level),
                        'mastery_status': PracticeAttempt.get_mastery_status(db.session, current_user.id, op, level)
                    }
    
    # Calculate multiplication table stats if available
    multiplication_stats = None
    if 'multiplication' in stats:
        mult_attempts = [a for a in attempts if a.operation == 'multiplication']
        multiplication_stats = {}
        for i in range(13):
            multiplication_stats[i] = {}
            for j in range(13):
                multiplication_stats[i][j] = {
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
                    multiplication_stats[i][j] = {
                        'attempts': len(relevant_attempts),
                        'correct': correct_count,
                        'accuracy': (correct_count / len(relevant_attempts)) * 100,
                        'average_time': sum(a.time_taken for a in relevant_attempts if a.time_taken is not None) / sum(1 for a in relevant_attempts if a.time_taken is not None)
                    }
    
    return render_template('progress.html',
                         stats=stats,
                         multiplication_stats=multiplication_stats,
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
