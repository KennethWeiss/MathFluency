from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from extensions import socketio
from models.quiz import Quiz, QuizParticipant
from models.user import User
from utils.math_problems import get_problem
from database import db  # Import db from database module
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
    return None

@socketio.on('join_quiz')
def handle_join_quiz(data):
    """Handle when a user joins a quiz"""
    logger.debug(f"Received join_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    if not quiz_id:
        logger.warning("No quiz_id provided")
        return
    
    # Join the quiz room
    room = f"quiz_{quiz_id}"
    join_room(room)
    logger.debug(f"User {current_user.username} joined room {room}")
    
    # Check if user is already a participant
    participant = QuizParticipant.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).first()
    
    if not participant:
        # Add user as participant
        participant = QuizParticipant(
            quiz_id=quiz_id,
            user_id=current_user.id,
            score=0
        )
        db.session.add(participant)
        db.session.commit()
        logger.debug(f"Added user {current_user.username} as participant")
    
    # Notify room that user joined
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
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
