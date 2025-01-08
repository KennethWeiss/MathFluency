from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from extensions import socketio
from models import db
from models.quiz import Quiz, QuizParticipant
from models.user import User
from utils.math_problems import get_problem
import random
import logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_quiz_problem(operation: str, level: int = None) -> dict:
    """Generate a problem for the quiz"""
    if level is None:
        # Default levels for each operation
        if operation == 'addition':
            level = random.randint(1, 5)
        elif operation == 'multiplication':
            level = random.randint(2, 9)  # Common multiplication tables
        else:
            level = 1
    
    problem = get_problem(operation, level)
    if problem:
        return {
            'text': problem['problem'],
            'answer': problem['answer']
        }
    else:
        logger.error(f"Failed to generate problem for operation {operation}, level {level}")
        return {
            'text': "Error generating problem",
            'answer': None
        }

@socketio.on('join_quiz')
def handle_join_quiz(data):
    """Handle when a user joins a quiz"""
    logger.debug(f"User {current_user.username} joining quiz with data: {data}")
    quiz_id = data.get('quiz_id')
    if not quiz_id:
        return
    
    # Join the quiz room
    room = f"quiz_{quiz_id}"
    join_room(room)
    logger.debug(f"User {current_user.username} joined room {room}")
    
    # If teacher, nothing else to do
    if current_user.is_teacher:
        return
    
    # For students, notify teacher of join
    quiz = Quiz.query.get(quiz_id)
    if quiz and quiz.status != 'finished':
        emit('user_joined', {
            'user': current_user.username,
            'quiz_id': quiz_id
        }, room=room)
        logger.debug(f"Notified room {room} that user {current_user.username} joined")
        
        # Send current leaderboard
        send_leaderboard(quiz_id)

@socketio.on('start_quiz')
def handle_start_quiz(data):
    """Handle when a teacher starts a quiz"""
    logger.debug(f"Received start_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    if not quiz_id or not current_user.is_teacher:
        logger.warning(f"Invalid start_quiz request: quiz_id={quiz_id}, is_teacher={current_user.is_teacher}")
        return
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz or quiz.teacher_id != current_user.id:
        logger.warning(f"Quiz not found or unauthorized: quiz_id={quiz_id}")
        return
    
    # Update quiz status
    quiz.status = 'active'
    db.session.commit()
    logger.debug(f"Quiz {quiz_id} status updated to active")
    
    # Generate first problem
    problem = generate_quiz_problem(quiz.operation)
    logger.debug(f"Generated first problem: {problem}")
    
    # Notify all participants
    room = f"quiz_{quiz_id}"
    emit('quiz_started', {
        'problem': problem['text'],
        'quiz_id': quiz_id
    }, room=room)
    logger.debug(f"Sent quiz_started event to room {room}")
    
    # Notify about status change
    emit('quiz_status_changed', {
        'status': 'active',
        'quiz_id': quiz_id
    }, room=room)
    logger.debug(f"Sent quiz_status_changed event to room {room}")

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Handle when a student submits an answer"""
    logger.debug(f"Received submit_answer event with data: {data}")
    quiz_id = data.get('quiz_id')
    answer = data.get('answer')
    problem = data.get('problem')
    
    if not all([quiz_id, answer is not None, problem]):
        logger.warning(f"Invalid submit_answer request: {data}")
        return
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz or quiz.status != 'active':
        logger.warning(f"Quiz not active: quiz_id={quiz_id}, status={quiz.status if quiz else 'None'}")
        return
    
    # Get participant
    participant = QuizParticipant.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        logger.warning(f"Participant not found: user={current_user.username}, quiz={quiz_id}")
        return
    
    try:
        # Generate new problem first
        level = participant.current_level if hasattr(participant, 'current_level') else None
        new_problem = generate_quiz_problem(quiz.operation, level)
        logger.debug(f"Generated new problem: {new_problem}")
        
        # Extract numbers from problem
        nums = [int(n) for n in problem.split() if n.isdigit()]
        if len(nums) != 2:
            logger.warning(f"Invalid problem format: {problem}")
            return
        
        # Calculate correct answer based on operation
        if quiz.operation == 'addition':
            correct = nums[0] + nums[1]
        elif quiz.operation == 'multiplication':
            correct = nums[0] * nums[1]
        else:
            logger.warning(f"Unsupported operation: {quiz.operation}")
            return
        
        # Check if answer is correct
        is_correct = int(answer) == correct
        
        # Update score if correct
        if is_correct:
            participant.score += 1
            # Increment level if adaptive mode is on and they've gotten several correct
            if quiz.adaptive and hasattr(participant, 'current_level'):
                consecutive_correct = getattr(participant, 'consecutive_correct', 0) + 1
                if consecutive_correct >= 3:  # Advance level after 3 correct answers
                    participant.current_level = min(participant.current_level + 1, 5)
                    participant.consecutive_correct = 0
                else:
                    participant.consecutive_correct = consecutive_correct
            db.session.commit()
            logger.debug(f"Updated score for user {current_user.username} in quiz {quiz_id}")
            
            # Send updated leaderboard
            send_leaderboard(quiz_id)
        elif hasattr(participant, 'consecutive_correct'):
            # Reset consecutive correct counter on wrong answer
            participant.consecutive_correct = 0
            db.session.commit()
        
        # Send feedback to student
        emit('answer_feedback', {
            'correct': is_correct,
            'quiz_id': quiz_id
        })
        
        # Send new problem
        emit('new_problem', {
            'problem': new_problem['text'],
            'quiz_id': quiz_id
        }, room=f"quiz_{quiz_id}")
        logger.debug(f"Sent new problem to quiz {quiz_id}")
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error processing answer: {e}")
        pass

@socketio.on('end_quiz')
def handle_end_quiz(data):
    """Handle when a teacher ends a quiz"""
    logger.debug(f"Received end_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    if not quiz_id or not current_user.is_teacher:
        logger.warning(f"Invalid end_quiz request: quiz_id={quiz_id}, is_teacher={current_user.is_teacher}")
        return
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz or quiz.teacher_id != current_user.id:
        logger.warning(f"Quiz not found or unauthorized: quiz_id={quiz_id}")
        return
    
    # Update quiz status
    quiz.status = 'finished'
    db.session.commit()
    logger.debug(f"Quiz {quiz_id} status updated to finished")
    
    # Get final scores
    participants = QuizParticipant.query\
        .filter_by(quiz_id=quiz_id)\
        .all()
    
    # Notify all participants
    room = f"quiz_{quiz_id}"
    for participant in participants:
        emit('quiz_ended', {
            'score': participant.score,
            'quiz_id': quiz_id
        }, room=room)
    logger.debug(f"Sent quiz_ended events to room {room}")
    
    # Notify about status change
    emit('quiz_status_changed', {
        'status': 'finished',
        'quiz_id': quiz_id
    }, room=room)
    logger.debug(f"Sent quiz_status_changed event to room {room}")

def send_leaderboard(quiz_id):
    """Send updated leaderboard to all participants"""
    participants = QuizParticipant.query\
        .filter_by(quiz_id=quiz_id)\
        .join(QuizParticipant.user)\
        .all()
    
    leaderboard = [{
        'username': p.user.username,
        'score': p.score
    } for p in participants]
    
    # Sort by score
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Send to all in room
    emit('leaderboard_update', {
        'leaderboard': leaderboard,
        'quiz_id': quiz_id
    }, room=f"quiz_{quiz_id}")
    logger.debug(f"Sent leaderboard update to quiz {quiz_id}")