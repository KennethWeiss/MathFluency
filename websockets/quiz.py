from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from extensions import socketio
from models.quiz import Quiz, QuizParticipant, QuizQuestion
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
    
    problem = get_problem(operation, level)  # Ensure this function returns a valid problem
    logger.debug(f"Generated problem: {problem['problem']}")  # Log the generated problem
    print("Generated problem in quiz.py: ", problem)
    if problem:
        return {
            'text': problem['problem'],
            'answer': problem['answer']
        }
    return None

def get_correct_answer(quiz_id, question_id):
    """Retrieve the correct answer for a given question in a quiz"""
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=quiz_id).first()
    if question:
        return question.answer
    return None

def send_leaderboard(quiz_id):
    """Send the current leaderboard to participants"""
    participants = QuizParticipant.query.filter_by(quiz_id=quiz_id).all()
    leaderboard = [{'username': User.query.get(p.user_id).username, 'score': p.score} for p in participants]
    
    # Sort leaderboard by score
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    emit('update_leaderboard', {'leaderboard': leaderboard}, room=f"quiz_{quiz_id}")
    logger.debug(f"Sent leaderboard for quiz {quiz_id}: {leaderboard}")

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
    
    # Get the quiz's operation from the database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.error(f"Quiz {quiz_id} not found")
        return
    
    # Generate and send a new problem using the quiz's operation
    problem = generate_quiz_problem(quiz.operation, quiz.level)
    emit('new_problem', {'quiz_id': quiz_id, 'problem': problem['text'], 'answer': problem['answer']}, room=f"quiz_{quiz_id}")
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
        logger.warning("User is not authenticated or not a teacher")
        return
    # Notify participants and start the quiz
    emit('quiz_started', {'quiz_id': quiz_id}, room=f"quiz_{quiz_id}")
    logger.debug(f"Quiz {quiz_id} started by {current_user.username}")

# Generate and send a new problem using the quiz's operation
    problem = generate_quiz_problem(quiz.operation, quiz.level)
    emit('new_problem', {'quiz_id': quiz_id, 'problem': problem['text']}, room=f"quiz_{quiz_id}")

@socketio.on('submit_answer')
def log_all_questions():
    """Log all questions and their answers for debugging."""
    questions = QuizQuestion.query.all()
    for question in questions:
        logger.debug(f"Question ID: {question.id}, Problem: {question.problem}, Answer: {question.answer}")

def handle_submit_answer(data):
    """Handle when a user submits an answer"""
    logger.debug(f"Received submit_answer event with data: {data}")
    quiz_id = data.get('quiz_id')
    submitted_answer = data.get('answer')
    question_id = data.get('question_id')

    # Fetch the correct answer from the database or quiz data
    correct_answer = get_correct_answer(quiz_id, question_id)
    print("=====================================")
    print("Submitted answer from quiz.py", submitted_answer)
    print(type(submitted_answer))
    print(correct_answer)
    print(type(correct_answer))
    print("=====================================")
    if submitted_answer == correct_answer:
        print("Correct answer")
        print("=====================================")
        # Update the user's score or quiz state
        participant = QuizParticipant.query.filter_by(
            quiz_id=quiz_id,
            user_id=current_user.id
        ).first()
        if participant:
            participant.score += 1  # Increment score for correct answer
            db.session.commit()
            logger.debug(f"Updated score for user {current_user.username} in quiz {quiz_id}")
        
        emit('answer_feedback', {'correct': True}, room=f"quiz_{quiz_id}")
    else:
        print("Incorrect answer")
        print("=====================================")
        emit('answer_feedback', {'correct': False}, room=f"quiz_{quiz_id}")

@socketio.on('end_quiz')
def handle_end_quiz(data):
    """Handle when a teacher ends a quiz"""
    logger.debug(f"Received end_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    # Logic to finalize the quiz, e.g., calculate final scores, notify participants
    emit('quiz_ended', {'quiz_id': quiz_id}, room=f"quiz_{quiz_id}")
    logger.debug(f"Quiz {quiz_id} ended by {current_user.username}")

@socketio.on('pause_quiz')
def handle_pause_quiz(data):
    """Handle when a teacher pauses a quiz"""
    logger.debug(f"Received pause_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    # Update the quiz status in the database
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        quiz.status = 'paused'
        db.session.commit()
        logger.debug(f"Quiz {quiz_id} paused by {current_user.username}")
    
    # Emit the status change
    emit('quiz_status_changed', {'quiz_id': quiz_id, 'status': 'paused'}, room=f"quiz_{quiz_id}")

@socketio.on('resume_quiz')
def handle_resume_quiz(data):
    """Handle when a teacher resumes a quiz"""
    logger.debug(f"Received resume_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    # Update the quiz status in the database
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        quiz.status = 'active'
        db.session.commit()
        logger.debug(f"Quiz {quiz_id} resumed by {current_user.username}")
        

        # Generate and send a new problem using the quiz's operation
        problem = generate_quiz_problem(quiz.operation, quiz.level)
        emit('new_problem', {'quiz_id': quiz_id, 'problem': problem['text']}, room=f"quiz_{quiz_id}")
    
    # Emit the status change
    emit('quiz_status_changed', {'quiz_id': quiz_id, 'status': 'active'}, room=f"quiz_{quiz_id}")
