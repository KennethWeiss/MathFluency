import random
from datetime import datetime, timedelta

def get_problem(operation, level, user_id=None, db=None):
    """
    Generate a math problem based on operation and level.
    If user_id and db are provided, consider user's history for adaptive difficulty.
    """
    if user_id and db:
        # Import here to avoid circular imports
        from models.practice_attempt import PracticeAttempt
        
        # Check if we should use a previously attempted problem
        if random.random() < 0.8:  # 80% chance to get a previous problem
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            # Get all attempts for this level and operation
            attempts_query = db.session.query(
                PracticeAttempt.problem,
                PracticeAttempt.correct_answer,
                db.func.count(PracticeAttempt.id).label('attempt_count'),
                db.func.sum(db.case((PracticeAttempt.is_correct == False, 1), else_=0)).label('incorrect_count')
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
                'incorrect_count'  # Order by fewest incorrect attempts first
            ).all()
            
            if attempts_query:
                # Prioritize problems with fewer mistakes
                # Take the first 3 problems (those with least mistakes) and choose one
                problem_pool = attempts_query[:3]
                chosen = random.choice(problem_pool)
                
                # Check for consecutive wrong attempts
                recent_attempts = db.session.query(PracticeAttempt).filter(
                    PracticeAttempt.user_id == user_id,
                    PracticeAttempt.problem == chosen.problem,
                    PracticeAttempt.created_at >= week_ago
                ).order_by(
                    PracticeAttempt.created_at.desc()
                ).limit(3).all()
                
                consecutive_wrong = 0
                for attempt in recent_attempts:
                    if not attempt.is_correct:
                        consecutive_wrong += 1
                    else:
                        break
                
                return {
                    'problem': chosen.problem,
                    'answer': chosen.correct_answer,
                    'show_answer': consecutive_wrong >= 3
                }
    
    if operation == 'addition':
        return generate_addition_problem(level)
    elif operation == 'multiplication':
        return generate_multiplication_problem(level)
    else:
        raise ValueError(f"Unsupported operation: {operation}")

def generate_addition_problem(level):
    """Generate addition problem based on level."""
    if level == 1:  # Adding 1 to single digit
        num1 = random.randint(1, 9)
        num2 = 1
    elif level == 2:  # Adding 2 to single digit
        num1 = random.randint(1, 9)
        num2 = 2
    elif level == 3:  # Make 10
        num1 = random.randint(1, 9)
        num2 = 10 - num1
    elif level == 4:  # Add single digit to double digit
        num1 = random.randint(10, 99)
        num2 = random.randint(1, 9)
    elif level == 5:  # Add double digit to double digit
        num1 = random.randint(10, 99)
        num2 = random.randint(10, 99)
    else:
        raise ValueError(f"Invalid addition level: {level}")
    
    return {
        'problem': f"{num1} + {num2}",
        'answer': num1 + num2
    }

def generate_multiplication_problem(level):
    """Generate multiplication problem for given table (level)."""
    if not 0 <= level <= 12:
        raise ValueError(f"Invalid multiplication level: {level}")
    
    num1 = level
    num2 = random.randint(0, 12)
    
    return {
        'problem': f"{num1} × {num2}",
        'answer': num1 * num2
    }