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
        week_ago = datetime.utcnow() - timedelta(days=ProblemGenerator.DAYS_TO_LOOK_BACK)
        
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
        Generate a math problem based on operation and level.
        If user_id and db are provided, consider user's history for adaptive difficulty.
        Excludes mastered problems from the problem set.
        """
        print(f"\nGenerating problem with: operation={operation}, level={level}")  # Debug log
        
        if operation not in ['addition', 'multiplication']:
            raise ValueError(f"Invalid operation: {operation}")
            
        try:
            level = int(level)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid level: {level}")

        mastered_problems = set()  # Initialize empty set for mastered problems

        if user_id and db:
            try:
                # Get all recent attempts for this level
                from models.practice_attempt import PracticeAttempt
                week_ago = datetime.utcnow() - timedelta(days=ProblemGenerator.DAYS_TO_LOOK_BACK)
                attempts_by_problem = db.session.query(
                    PracticeAttempt.problem,
                    PracticeAttempt.correct_answer,
                    db.func.count(PracticeAttempt.id).label('attempt_count'),
                    db.func.sum(
                        db.case((PracticeAttempt.is_correct == True, 1), else_=0)
                    ).label('correct_count')
                ).filter(
                    PracticeAttempt.user_id == user_id,
                    PracticeAttempt.operation == operation,
                    PracticeAttempt.level == level,
                    PracticeAttempt.created_at >= week_ago
                ).group_by(
                    PracticeAttempt.problem,
                    PracticeAttempt.correct_answer
                ).all()

                # Identify mastered problems
                for attempt in attempts_by_problem:
                    if (attempt.attempt_count >= PracticeAttempt.MIN_ATTEMPTS and
                        attempt.correct_count / attempt.attempt_count >= PracticeAttempt.MASTERY_THRESHOLD):
                        mastered_problems.add(attempt.problem)

                print(f"Found {len(mastered_problems)} mastered problems")  # Debug log

                # Try to select a practice problem that isn't mastered
                if random.random() < ProblemGenerator.PRACTICE_PROBABILITY:
                    print("Attempting to get practice problem")  # Debug log
                    attempts = ProblemGenerator.get_recent_attempts(db, user_id, operation, level)
                    
                    if attempts:
                        print(f"Found {len(attempts)} recent attempts")  # Debug log
                        # Filter out mastered problems and choose from remaining
                        unmastered_attempts = [a for a in attempts if a.problem not in mastered_problems]
                        if unmastered_attempts:
                            chosen = random.choice(unmastered_attempts[:ProblemGenerator.TOP_PROBLEMS_TO_CONSIDER])
                            consecutive_wrong = ProblemGenerator.check_consecutive_wrong(
                                db, user_id, chosen.problem
                            )
                            
                            print(f"Selected practice problem: {chosen.problem}")  # Debug log
                            return ProblemGenerator.create_problem(
                                chosen.problem,
                                chosen.correct_answer,
                                consecutive_wrong >= ProblemGenerator.CONSECUTIVE_WRONG_THRESHOLD
                            )
                        else:
                            print("All practice problems are mastered, generating new problem")  # Debug log
                    else:
                        print("No recent attempts found, generating new problem")  # Debug log
                        
            except Exception as e:
                print(f"Error in practice problem selection: {e}")  # Debug log
                import traceback
                print(traceback.format_exc())  # Print full stack trace
        
        # Generate new problem if no history or didn't select practice problem
        print(f"Generating new {operation} problem for level {level}")  # Debug log
        
        # Keep generating problems until we find one that isn't mastered
        max_attempts = 10  # Prevent infinite loop
        for _ in range(max_attempts):
            if operation == 'addition':
                problem = ProblemGenerator.generate_addition_problem(level)
            elif operation == 'multiplication':
                problem = ProblemGenerator.generate_multiplication_problem(level)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            if user_id and db and problem['problem'] in mastered_problems:
                print(f"Generated problem {problem['problem']} is mastered, trying again")
                continue
            
            return problem
            
        # If we couldn't find an unmastered problem after max_attempts, return the last generated one
        print(f"Could not find unmastered problem after {max_attempts} attempts")
        return problem