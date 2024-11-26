from app import app, db
from models.practice_attempt import PracticeAttempt

with app.app_context():
    attempts = PracticeAttempt.query.order_by(PracticeAttempt.created_at.desc()).limit(5).all()
    print('\nLast 5 Practice Attempts:\n')
    for a in attempts:
        print(f'Problem: {a.problem}')
        print(f'User Answer: {a.user_answer}')
        print(f'Correct Answer: {a.correct_answer}')
        print(f'Correct: {a.is_correct}')
        print(f'Time: {a.time_taken:.1f}s')
        print(f'Created: {a.created_at}')
        print('-' * 50)
