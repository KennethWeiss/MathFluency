from datetime import datetime, timedelta
from typing import Dict, Union, Optional, List, Tuple
from utils.math_problems import get_problem as get_math_problem
from sqlalchemy import or_
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases for clarity
Problem = Dict[str, Union[str, int, bool, float]]

class PracticeTracker:
    """Tracks user practice attempts and manages problem selection based on mastery."""
    
    # Problem mastery thresholds
    MIN_ATTEMPTS = 3  # Minimum attempts before considering mastery
    MASTERY_THRESHOLD = 0.8  # 80% accuracy threshold
    DAYS_TO_LOOK_BACK = 7  # Only look at last 7 days of attempts
    
    # Level mastery thresholds (from ProgressService)
    LEVEL_UP_ACCURACY = 0.9   # 90% accuracy needed to level up
    LEVEL_UP_TIME = 5.0       # Must solve in under 5 seconds to level up
    RECENT_ATTEMPTS_TO_CHECK = 10  # Check last 10 attempts for level up

    @staticmethod
    def get_problem_stats(db, user_id: int, operation: str, level: int) -> Dict[str, Dict]:
        """Get statistics for all attempted problems at this level."""
        from models.practice_attempt import PracticeAttempt
        week_ago = datetime.utcnow() - timedelta(days=PracticeTracker.DAYS_TO_LOOK_BACK)
        
        # Get all attempts for this level in the last week
        attempts = db.session.query(
            PracticeAttempt.problem,
            PracticeAttempt.correct_answer,
            PracticeAttempt.is_correct,
            PracticeAttempt.time_taken
        ).filter(
            PracticeAttempt.user_id == user_id,
            PracticeAttempt.operation == operation,
            PracticeAttempt.level == level,
            PracticeAttempt.created_at >= week_ago
        ).all()

        # Group attempts by problem
        problems = {}
        for attempt in attempts:
            prob = attempt.problem
            if operation == 'multiplication':
                # Normalize multiplication problem format (always put smaller number first)
                n1, n2 = map(int, prob.split(' × '))
                prob = f"{min(n1, n2)} × {max(n1, n2)}"
            
            if prob not in problems:
                problems[prob] = {
                    'attempts': 0,
                    'correct': 0,
                    'total_time': 0,
                    'answer': attempt.correct_answer
                }
            problems[prob]['attempts'] += 1
            if attempt.is_correct:
                problems[prob]['correct'] += 1
            if attempt.time_taken:
                problems[prob]['total_time'] += attempt.time_taken

        # Calculate accuracy and average time for each problem
        for prob in problems:
            stats = problems[prob]
            stats['accuracy'] = stats['correct'] / stats['attempts']
            stats['avg_time'] = stats['total_time'] / stats['attempts']
            
        return problems

    @staticmethod
    def is_problem_mastered(stats: Dict) -> bool:
        """Check if a problem has been mastered."""
        return (stats['attempts'] >= PracticeTracker.MIN_ATTEMPTS and 
                stats['accuracy'] >= PracticeTracker.MASTERY_THRESHOLD)

    @staticmethod
    def check_level_mastery(db, user_id: int, operation: str, level: int) -> Tuple[bool, float, float]:
        """
        Check if a student has mastered the current level.
        A level is mastered when:
        1. Recent performance shows high accuracy and speed (90% accuracy, <5s per problem)
        2. All problems in the level have been mastered (80% accuracy over at least 3 attempts)
        
        Returns: (should_level_up, accuracy, avg_time)
        """
        from models.practice_attempt import PracticeAttempt
        import logging
        
        logging.info(f"\nChecking level mastery for {operation} level {level}")
        
        # First check recent performance
        recent_attempts = db.session.query(PracticeAttempt).filter_by(
            user_id=user_id,
            operation=operation,
            level=level
        ).order_by(
            PracticeAttempt.created_at.desc()
        ).limit(PracticeTracker.RECENT_ATTEMPTS_TO_CHECK).all()

        logging.info(f"Found {len(recent_attempts)} recent attempts")
        
        if len(recent_attempts) < PracticeTracker.RECENT_ATTEMPTS_TO_CHECK:
            logging.info("Not enough recent attempts for level mastery")
            return False, 0, float('inf')

        # Calculate recent accuracy and average time
        correct_count = sum(1 for a in recent_attempts if a.is_correct)
        accuracy = correct_count / len(recent_attempts)
        
        correct_times = [a.time_taken for a in recent_attempts if a.is_correct and a.time_taken]
        avg_time = sum(correct_times) / len(correct_times) if correct_times else float('inf')
        
        logging.info(f"Recent performance: accuracy={accuracy:.1%}, avg_time={avg_time:.1f}s")

        # Check if recent performance meets level up criteria
        recent_mastery = (accuracy >= PracticeTracker.LEVEL_UP_ACCURACY and 
                         avg_time < PracticeTracker.LEVEL_UP_TIME)
        
        if not recent_mastery:
            logging.info("Recent performance does not meet level up criteria")
            return False, accuracy, avg_time

        # Then check if all problems in the level are mastered
        problem_stats = PracticeTracker.get_problem_stats(db, user_id, operation, level)
        
        # For multiplication, we need to check all combinations for this level
        if operation == 'multiplication':
            required_problems = set()
            for i in range(0, 13):  # 0-12 for each level
                problem = f"{min(i, level)} × {max(i, level)}"
                required_problems.add(problem)
            
            logging.info(f"Required problems for multiplication level {level}: {required_problems}")
            
            # Check each required problem
            for problem in required_problems:
                if problem not in problem_stats:
                    logging.info(f"Problem {problem} has not been attempted yet")
                    return False, accuracy, avg_time
                
                stats = problem_stats[problem]
                if not PracticeTracker.is_problem_mastered(stats):
                    logging.info(f"Problem {problem} is not yet mastered: "
                               f"{stats['attempts']} attempts, {stats['accuracy']:.1%} accuracy")
                    return False, accuracy, avg_time
        
        # For other operations, check if we have enough mastered problems
        else:
            mastered_count = sum(1 for stats in problem_stats.values() 
                               if PracticeTracker.is_problem_mastered(stats))
            min_mastered = 10  # Require at least 10 mastered problems for non-multiplication
            
            logging.info(f"Mastered {mastered_count} problems out of {len(problem_stats)}")
            
            if mastered_count < min_mastered:
                logging.info(f"Not enough mastered problems (need {min_mastered})")
                return False, accuracy, avg_time

        logging.info("All criteria met - student has mastered this level!")
        return True, accuracy, avg_time

    @staticmethod
    def get_problem(operation: str, level: int, user_id: Optional[int] = None, 
                db = None) -> Problem:
        """Get a problem, excluding mastered ones."""
        import random
        from utils.math_problems import get_problem as get_math_problem
        import logging

        # If no user tracking needed, return a random problem
        if not user_id or not db:
            return get_math_problem(operation, level)

        # First check if student should level up
        should_level_up, accuracy, avg_time = PracticeTracker.check_level_mastery(
            db, user_id, operation, level
        )
        
        if should_level_up:
            logging.info(f"Student has mastered level {level} "
                        f"(accuracy: {accuracy:.1%}, avg_time: {avg_time:.1f}s)")
            max_level = 5 if operation == 'addition' else 12
            new_level = min(level + 1, max_level)
            if new_level != level:
                return {
                    'level_up': True,
                    'new_level': new_level,
                    'accuracy': accuracy * 100,
                    'avg_time': avg_time
                }

        # Get stats for all problems attempted at this level
        problem_stats = PracticeTracker.get_problem_stats(db, user_id, operation, level)
        
        # Log current problem statistics
        logging.info(f"\nProblem statistics for {operation} level {level}:")
        for prob, stats in problem_stats.items():
            logging.info(f"{prob}: {stats['attempts']} attempts, {stats['accuracy']:.1%} accuracy" + 
                      f" {'(MASTERED)' if PracticeTracker.is_problem_mastered(stats) else ''}")

        # Try up to 10 times to get an unmastered problem
        for _ in range(10):
            problem = get_math_problem(operation, level)
            prob_str = problem['problem']
            
            # If multiplication, normalize the format
            if operation == 'multiplication':
                n1, n2 = map(int, prob_str.split(' × '))
                prob_str = f"{min(n1, n2)} × {max(n1, n2)}"
            
            # Check if this problem has been mastered
            if prob_str in problem_stats:
                stats = problem_stats[prob_str]
                if PracticeTracker.is_problem_mastered(stats):
                    logging.info(f"Skipping mastered problem: {prob_str}")
                    continue
            
            logging.info(f"Selected problem: {problem['problem']}")
            return problem

        # If we couldn't find an unmastered problem after 10 tries,
        # get a completely new problem that hasn't been attempted
        while True:
            problem = get_math_problem(operation, level)
            prob_str = problem['problem']
            if prob_str not in problem_stats:
                logging.info(f"Selected new unattempted problem: {problem['problem']}")
                return problem