from flask import session
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from extensions import socketio
from models.quiz import Quiz, QuizParticipant, QuizQuestion, QuizAnswer
from models.user import User
from models.practice_attempt import PracticeAttempt
from utils.math_problems import get_problem
from utils.practice_tracker import PracticeTracker
from database import db
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
    logger.debug(f"Querying for correct answer with quiz_id: {quiz_id}, question_id: {question_id}")
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
    
    # Save the question to the database
    question = QuizQuestion(
        quiz_id=quiz_id,
        problem=problem['text'],
        answer=problem['answer'],
        level=quiz.level
    )
    db.session.add(question)
    db.session.commit()
    
    emit('new_problem', {
        'quiz_id': quiz_id,
        'problem': problem['text'],
        'question_id': question.id,  # Send the question ID to the client
        'answer': problem['answer'],  # Pass the correct answer directly
    }, room=f"quiz_{quiz_id}")
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
        
    # Get the quiz from database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.warning(f"Quiz {quiz_id} not found")
        return
        
    # Update quiz status
    quiz.status = 'active'
    db.session.commit()
    
    # Notify all participants about the status change
    emit('quiz_status_changed', {
        'quiz_id': quiz_id,
        'status': 'active'
    }, room=f"quiz_{quiz_id}")
    
    # Generate and send a new problem
    problem = generate_quiz_problem(quiz.operation, quiz.level)
    
    # Save the question to the database
    question = QuizQuestion(
        quiz_id=quiz_id,
        problem=problem['text'],
        answer=problem['answer'],
        level=quiz.level
    )
    db.session.add(question)
    db.session.commit()
    
    emit('new_problem', {
        'quiz_id': quiz_id,
        'problem': problem['text'],
        'question_id': question.id,  # Send the question ID to the client
        'answer': problem['answer'],  # Pass the correct answer directly
    }, room=f"quiz_{quiz_id}")
    
    logger.debug(f"Quiz {quiz_id} started by {current_user.username}")

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Handle when a user submits an answer"""
    logger.debug(f"Received submit_answer event with data: {data}")
    quiz_id = data.get('quiz_id')
    submitted_answer = data.get('answer')
    question_id = data.get('question_id')
    correct_answer = get_correct_answer(quiz_id, question_id)
   
    logger.debug(f"Submitted answer: {submitted_answer} (type: {type(submitted_answer)})")
    logger.debug(f"Correct answer: {correct_answer} (type: {type(correct_answer)})")
    print("Submitted answer: ", submitted_answer)
    print("Correct answer: ", correct_answer)
    print("data: ", data)
    print("=====================================")
    
    # Get the quiz to know the operation and level
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.error(f"Quiz {quiz_id} not found")
        return
        
    # Get the question to record the problem
    question = QuizQuestion.query.get(question_id)
    if not question:
        logger.error(f"Question {question_id} not found")
        return
    
    is_correct = str(submitted_answer) == str(correct_answer)
    
    # Create a QuizAnswer record
    participant = QuizParticipant.query.filter_by(
        quiz_id=quiz_id,
        user_id=current_user.id
    ).first()
    
    if participant:
        # Record the answer in quiz history
        answer = QuizAnswer(
            participant_id=participant.id,
            question_id=question_id,
            answer=submitted_answer,
            correct=is_correct,
            time_taken=data.get('time_taken', 0)
        )
        db.session.add(answer)
        
        # Update quiz score if correct
        if is_correct:
            participant.score += 1
        
        # Record in practice history for overall stats
        practice_attempt = PracticeAttempt(
            user_id=current_user.id,
            operation=quiz.operation,
            level=quiz.level,
            problem=question.problem,
            user_answer=submitted_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            time_taken=data.get('time_taken', 0)
        )
        db.session.add(practice_attempt)
        
        # For multiplication, add commutative case
        if quiz.operation == 'multiplication':
            num1, num2 = map(int, question.problem.split('×'))
            if num1 != num2:  # Only if numbers are different
                commutative_problem = f"{num2} × {num1}"
                commutative_attempt = PracticeAttempt(
                    user_id=current_user.id,
                    operation=quiz.operation,
                    level=max(num1, num2),
                    problem=commutative_problem,
                    user_answer=submitted_answer,
                    correct_answer=correct_answer,
                    is_correct=is_correct,
                    time_taken=data.get('time_taken', 0)
                )
                db.session.add(commutative_attempt)
        
        db.session.commit()
        
        if is_correct:
            # Generate and send a new problem
            problem = generate_quiz_problem(quiz.operation, quiz.level)
            
            # Save the question to the database
            new_question = QuizQuestion(
                quiz_id=quiz_id,
                problem=problem['text'],
                answer=problem['answer'],
                level=quiz.level
            )
            db.session.add(new_question)
            db.session.commit()
            
            emit('new_problem', {
                'quiz_id': quiz_id,
                'problem': problem['text'],
                'question_id': new_question.id,
                'answer': problem['answer']
            }, room=f"quiz_{quiz_id}")
            emit('score_updated', {'score': participant.score}, room=f"quiz_{quiz_id}")
            send_leaderboard(quiz_id)
            emit('answer_feedback', {'correct': True}, room=f"quiz_{quiz_id}")
    else:
        print("Incorrect answer")
        print("=====================================")
        emit('answer_feedback', {'correct': False}, room=f"quiz_{quiz_id}")

@socketio.on('pause_quiz')
def handle_pause_quiz(data):
    """Handle when a teacher pauses a quiz"""
    logger.debug(f"Received pause_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
        logger.warning("User is not authenticated or not a teacher")
        return
        
    # Get the quiz from database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.warning(f"Quiz {quiz_id} not found")
        return
        
    # Update quiz status
    quiz.status = 'paused'
    db.session.commit()
    
    # Notify all participants about the status change
    emit('quiz_status_changed', {
        'quiz_id': quiz_id,
        'status': 'paused'
    }, room=f"quiz_{quiz_id}")
    
    logger.debug(f"Quiz {quiz_id} paused by {current_user.username}")

@socketio.on('resume_quiz')
def handle_resume_quiz(data):
    """Handle when a teacher resumes a quiz"""
    logger.debug(f"Received resume_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
        logger.warning("User is not authenticated or not a teacher")
        return
        
    # Get the quiz from database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.warning(f"Quiz {quiz_id} not found")
        return
        
    # Update quiz status
    quiz.status = 'active'
    db.session.commit()
    
    # Generate and send a new problem
    problem = generate_quiz_problem(quiz.operation, quiz.level)
    
    # Save the question to the database
    question = QuizQuestion(
        quiz_id=quiz_id,
        problem=problem['text'],
        answer=problem['answer'],
        level=quiz.level
    )
    db.session.add(question)
    db.session.commit()
    
    emit('new_problem', {
        'quiz_id': quiz_id,
        'problem': problem['text'],
        'question_id': question.id,  # Send the question ID to the client
        'answer': problem['answer'],  # Pass the correct answer directly
    }, room=f"quiz_{quiz_id}")
    
    # Notify all participants about the status change
    emit('quiz_status_changed', {
        'quiz_id': quiz_id,
        'status': 'active'
    }, room=f"quiz_{quiz_id}")
    
    logger.debug(f"Quiz {quiz_id} resumed by {current_user.username}")

@socketio.on('end_quiz')
def handle_end_quiz(data):
    """Handle when a teacher ends a quiz"""
    logger.debug(f"Received end_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
        logger.warning("User is not authenticated or not a teacher")
        return
        
    # Get the quiz from database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.warning(f"Quiz {quiz_id} not found")
        return
        
    # Update quiz status
    quiz.status = 'finished'
    db.session.commit()
    
    # Notify all participants about the status change
    emit('quiz_status_changed', {
        'quiz_id': quiz_id,
        'status': 'finished'
    }, room=f"quiz_{quiz_id}")
    
    logger.debug(f"Quiz {quiz_id} ended by {current_user.username}")

@socketio.on('restart_quiz')
def handle_restart_quiz(data):
    """Handle when a teacher restarts a quiz"""
    logger.debug(f"Received restart_quiz event with data: {data}")
    quiz_id = data.get('quiz_id')
    
    if not quiz_id or not current_user.is_authenticated or not current_user.is_teacher:
        logger.warning("User is not authenticated or not a teacher")
        return
        
    # Get the quiz from database
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        logger.warning(f"Quiz {quiz_id} not found")
        return

    # Reset quiz state
    quiz.status = 'waiting'
    
    # Reset participant scores
    participants = QuizParticipant.query.filter_by(quiz_id=quiz_id).all()
    for participant in participants:
        participant.score = 0
    db.session.commit()
    
    # Notify all participants about the status change
    emit('quiz_status_changed', {
        'quiz_id': quiz_id,
        'status': 'waiting'
    }, room=f"quiz_{quiz_id}")
    
    logger.debug(f"Quiz {quiz_id} restarted by {current_user.username}")
