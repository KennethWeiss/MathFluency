from datetime import datetime, timedelta
from typing import Dict, Union, Optional, List
from utils.math_problems import get_problem as get_math_problem

# Type aliases for clarity
Problem = Dict[str, Union[str, int, bool]]

class PracticeTracker:
    """Tracks user practice attempts and manages problem selection based on mastery."""
    
    PRACTICE_PROBABILITY = 0.3
    CONSECUTIVE_WRONG_THRESHOLD = 3
    DAYS_TO_LOOK_BACK = 7
    TOP_PROBLEMS_TO_CONSIDER = 3

    @staticmethod
    def get_recent_attempts(db, user_id: int, operation: str, level: int, 
                          days: int = DAYS_TO_LOOK_BACK) -> List:
        """Get recent practice attempts for a user."""
        from models.practice_attempt import PracticeAttempt
        week_ago = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            PracticeAttempt.problem,
            PracticeAttempt.correct_answer,
            db.func.count(PracticeAttempt.id).label('attempt_count'),
            db.func.sum(
                db.case((PracticeAttempt.is_correct == False, 1), else_=0)
            ).label('incorrect_count')
        ).filter(
            PracticeAttempt.user_id == user_id,
            PracticeAttempt.operation == operation,
            PracticeAttempt.level == level,
            PracticeAttempt.created_at >= week_ago
        ).group_by(
            PracticeAttempt.problem,
            PracticeAttempt.correct_answer
        ).having(
            db.func.sum(db.case((PracticeAttempt.is_correct == False, 1), else_=0)) > 0
        ).order_by(
            'incorrect_count DESC'  # Order by most incorrect attempts first
        ).all()

    @staticmethod
    def check_consecutive_wrong(db, user_id: int, problem: str) -> int:
        """Check number of consecutive wrong attempts for a problem."""
        from models.practice_attempt import PracticeAttempt
        week_ago = datetime.utcnow() - timedelta(days=PracticeTracker.DAYS_TO_LOOK_BACK)
        
        recent_attempts = db.session.query(PracticeAttempt).filter(
            PracticeAttempt.user_id == user_id,
            PracticeAttempt.problem == problem,
            PracticeAttempt.created_at >= week_ago
        ).order_by(
            PracticeAttempt.created_at.desc()
        ).limit(3).all()
        
        return sum(1 for attempt in recent_attempts if not attempt.is_correct)

    @staticmethod
    def get_problem(operation: str, level: int, user_id: Optional[int] = None, 
                   db = None) -> Problem:
        """
        Get a problem based on user's history and mastery level.
        If user_id and db are provided, considers user's history for adaptive difficulty.
        """
        # Get a new problem from math_problems.py
        problem = get_math_problem(operation, level)
        if not problem:
            return None
            
        # If no user tracking needed, return the problem as is
        if not user_id or not db:
            return problem
            
        # Get recent attempts to find problems that need more practice
        recent_attempts = PracticeTracker.get_recent_attempts(db, user_id, operation, level)
        
        # If there are problems with consecutive wrong attempts, prioritize those
        for attempt in recent_attempts:
            consecutive_wrong = PracticeTracker.check_consecutive_wrong(
                db, user_id, attempt.problem
            )
            if consecutive_wrong >= PracticeTracker.CONSECUTIVE_WRONG_THRESHOLD:
                return {
                    'problem': attempt.problem,
                    'answer': attempt.correct_answer,
                    'needs_practice': True
                }
        
        return problem