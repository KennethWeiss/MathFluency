from datetime import datetime, timedelta
import random
from typing import Dict, Optional, Union, List

# Type aliases for clarity
Problem = Dict[str, Union[str, int, bool]]
Number = Union[int, float]

class ProblemGenerator:
    PRACTICE_PROBABILITY = 0.3
    CONSECUTIVE_WRONG_THRESHOLD = 3
    DAYS_TO_LOOK_BACK = 7
    TOP_PROBLEMS_TO_CONSIDER = 3

    @staticmethod
    def create_problem(problem: str, answer: Number, show_answer: bool = False) -> Problem:
        """Create a standardized problem dictionary."""
        return {
            'problem': problem,
            'answer': answer,
            'show_answer': show_answer
        }

    @staticmethod
    def generate_addition_problem(level: int) -> Problem:
        """Generate addition problem matching client-side logic."""
        level = int(level)
        
        def get_numbers(level: int) -> tuple[int, int]:
            if level == 1:  # Adding 1 to single digit
                return random.randint(1, 9), 1
            elif level == 2:  # Adding 2 to single digit
                return random.randint(1, 9), 2
            elif level == 3:  # Making 10
                num1 = random.randint(1, 9)
                return num1, 10 - num1
            elif level == 4:  # Add single digit to double digit
                return random.randint(10, 99), random.randint(1, 9)
            elif level == 5:  # Add double digit to double digit
                return random.randint(10, 99), random.randint(10, 99)
            else:
                raise ValueError(f"Invalid addition level: {level}")
        
        num1, num2 = get_numbers(level)
        return ProblemGenerator.create_problem(f"{num1} + {num2}", num1 + num2)

    @staticmethod
    def generate_multiplication_problem(level: int) -> Problem:
        """Generate multiplication problem matching client-side logic."""
        level = int(level)
        
        if 0 <= level <= 12:
            num = random.randint(0, 12)
            return ProblemGenerator.create_problem(f"{num} × {level}", num * level)
        else:
            raise ValueError(f"Invalid multiplication level: {level}")

    @staticmethod
    def get_recent_attempts(db, user_id: int, operation: str, level: int, 
                          days: int = DAYS_TO_LOOK_BACK) -> List:
        """Get recent practice attempts for a user."""
        week_ago = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            db.models.PracticeAttempt.problem,
            db.models.PracticeAttempt.correct_answer,
            db.func.count(db.models.PracticeAttempt.id).label('attempt_count'),
            db.func.sum(
                db.case((db.models.PracticeAttempt.is_correct == False, 1), else_=0)
            ).label('incorrect_count')
        ).filter(
            db.models.PracticeAttempt.user_id == user_id,
            db.models.PracticeAttempt.operation == operation,
            db.models.PracticeAttempt.level == level,
            db.models.PracticeAttempt.created_at >= week_ago
        ).group_by(
            db.models.PracticeAttempt.problem,
            db.models.PracticeAttempt.correct_answer
        ).having(
            db.func.sum(db.case((db.models.PracticeAttempt.is_correct == False, 1), else_=0)) > 0
        ).order_by(
            'incorrect_count DESC'  # Order by most incorrect attempts first
        ).all()

    @staticmethod
    def check_consecutive_wrong(db, user_id: int, problem: str) -> int:
        """Check number of consecutive wrong attempts for a problem."""
        week_ago = datetime.utcnow() - timedelta(days=ProblemGenerator.DAYS_TO_LOOK_BACK)
        
        recent_attempts = db.session.query(db.models.PracticeAttempt).filter(
            db.models.PracticeAttempt.user_id == user_id,
            db.models.PracticeAttempt.problem == problem,
            db.models.PracticeAttempt.created_at >= week_ago
        ).order_by(
            db.models.PracticeAttempt.created_at.desc()
        ).limit(3).all()
        
        return sum(1 for attempt in recent_attempts if not attempt.is_correct)

def get_problem(operation: str, level: int, user_id: Optional[int] = None, 
                db = None) -> Problem:
    """
    Generate a math problem based on operation and level.
    If user_id and db are provided, consider user's history for adaptive difficulty.
    """
    if user_id and db:
        if random.random() < ProblemGenerator.PRACTICE_PROBABILITY:
            attempts = ProblemGenerator.get_recent_attempts(db, user_id, operation, level)
            
            if attempts:
                # Choose from top challenging problems
                chosen = random.choice(attempts[:ProblemGenerator.TOP_PROBLEMS_TO_CONSIDER])
                consecutive_wrong = ProblemGenerator.check_consecutive_wrong(
                    db, user_id, chosen.problem
                )
                
                return ProblemGenerator.create_problem(
                    chosen.problem,
                    chosen.correct_answer,
                    consecutive_wrong >= ProblemGenerator.CONSECUTIVE_WRONG_THRESHOLD
                )
    
    # Generate new problem if no history or didn't select practice problem
    if operation == 'addition':
        return ProblemGenerator.generate_addition_problem(level)
    elif operation == 'multiplication':
        return ProblemGenerator.generate_multiplication_problem(level)
    else:
        raise ValueError(f"Unsupported operation: {operation}")