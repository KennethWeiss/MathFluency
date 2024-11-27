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
        
        # Check if we should use a previously missed problem
        if random.random() < 0.3:  # 30% chance to get a missed problem
            week_ago = datetime.utcnow() - timedelta(days=7)
            missed_problems = db.session.query(PracticeAttempt).filter(
                PracticeAttempt.user_id == user_id,
                PracticeAttempt.operation == operation,
                PracticeAttempt.level == level,
                PracticeAttempt.is_correct == False,
                PracticeAttempt.created_at >= week_ago
            ).all()
            
            if missed_problems:
                # Pick a random missed problem
                missed_attempt = random.choice(missed_problems)
                return {
                    'problem': missed_attempt.problem,
                    'answer': missed_attempt.correct_answer
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