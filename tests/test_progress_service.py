import pytest
from datetime import datetime, timedelta
from database import db
from models.practice_attempt import PracticeAttempt
from models.user import User
from services.progress_service import ProgressService
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            is_teacher=False
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_attempts(app, test_user):
    with app.app_context():
        # Create some test attempts
        attempts = [
            # Mastered level (90% accuracy)
            PracticeAttempt(
                user_id=test_user.id,
                operation='multiplication',
                level=1,
                problem='2 × 3',
                user_answer=6,
                correct_answer=6,
                is_correct=True,
                time_taken=3.0
            ) for _ in range(9)  # 9 correct attempts
        ]
        # Add one incorrect attempt
        attempts.append(
            PracticeAttempt(
                user_id=test_user.id,
                operation='multiplication',
                level=1,
                problem='2 × 3',
                user_answer=5,
                correct_answer=6,
                is_correct=False,
                time_taken=4.0
            )
        )
        
        for attempt in attempts:
            db.session.add(attempt)
        db.session.commit()
        return attempts

def test_get_student_stats(app, test_user, test_attempts):
    with app.app_context():
        stats = ProgressService.get_student_stats(test_user.id, 'multiplication')
        
        assert stats['total_attempts'] == 10
        assert stats['accuracy'] == 90.0
        assert stats['current_streak'] == 0  # Last attempt was incorrect
        assert 3.0 <= stats['average_time'] <= 4.0
        
        # Check level stats
        level_stats = stats['levels']['1']
        assert level_stats['attempts'] == 10
        assert level_stats['correct'] == 9
        assert level_stats['accuracy'] == 90.0
        assert level_stats['mastery_status'] == 'mastered'

def test_should_change_level(app, test_user, test_attempts):
    with app.app_context():
        # Should level up with 90% accuracy and good time
        should_change, new_level = ProgressService.should_change_level(
            test_user.id, 'multiplication', 1
        )
        assert should_change
        assert new_level == 2

def test_analyze_missed_problems(app, test_user, test_attempts):
    with app.app_context():
        problems = ProgressService.analyze_missed_problems(test_user.id)
        assert len(problems) == 1
        assert problems[0]['problem'] == '2 × 3'
        assert problems[0]['count'] == 1

def test_get_multiplication_table_stats(app, test_user, test_attempts):
    with app.app_context():
        stats = ProgressService.get_multiplication_table_stats(test_user.id)
        
        # Check the 2×3 entry
        assert stats[2][3]['attempts'] == 10
        assert stats[2][3]['correct'] == 9
        assert stats[2][3]['accuracy'] == 90.0
