from models.practice_attempt import PracticeAttempt
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func
from utils.math_problems import get_problem

class ProgressService:
    # Constants for mastery levels
    MIN_ATTEMPTS = 3
    MASTERY_THRESHOLD = 0.8  # 80%
    LEARNING_THRESHOLD = 0.6  # 60%
    LEVEL_UP_ACCURACY = 0.9   # 90%
    LEVEL_UP_TIME = 5.0       # 5 seconds
    LEVEL_DOWN_ACCURACY = 0.7  # 70%

    @staticmethod
    def get_student_stats(student_id: int, operation: Optional[str] = None) -> Dict:
        """Calculate comprehensive statistics for a student's practice attempts"""
        # Get attempts for the specified operation
        query = PracticeAttempt.query.filter_by(user_id=student_id)
        if operation:
            query = query.filter_by(operation=operation)
        attempts = query.all()
        
        if not attempts:
            return {
                'total_attempts': 0,
                'accuracy': 0,
                'current_streak': 0,
                'average_time': 0,
                'fastest_time': 0,
                'levels': {}
            }
        
        # Calculate basic stats
        total_attempts = len(attempts)
        correct_attempts = len([a for a in attempts if a.is_correct])
        accuracy = (correct_attempts / total_attempts * 100)
        
        # Calculate streak
        current_streak = 0
        for attempt in reversed(attempts):
            if attempt.is_correct:
                current_streak += 1
            else:
                break
        
        # Calculate timing stats
        correct_times = [a.time_taken for a in attempts if a.is_correct and a.time_taken is not None]
        avg_time = sum(correct_times) / len(correct_times) if correct_times else 0
        fastest_time = min(correct_times) if correct_times else 0
        
        # Calculate level stats
        level_stats = {}
        for level in set(a.level for a in attempts):
            level_attempts = [a for a in attempts if a.level == level]
            problem = get_problem(operation, level) if operation else None
            description = problem['description'] if problem else f"Level {level}"
            level_stats[str(level)] = ProgressService.calculate_level_stats(level_attempts, description)
        
        return {
            'total_attempts': total_attempts,
            'accuracy': accuracy,
            'current_streak': current_streak,
            'average_time': avg_time,
            'fastest_time': fastest_time,
            'levels': level_stats
        }

    @staticmethod
    def calculate_level_stats(attempts: List[PracticeAttempt], description: str) -> Dict:
        """Calculate detailed statistics for a specific level"""
        total = len(attempts)
        correct = len([a for a in attempts if a.is_correct])
        times = [a.time_taken for a in attempts if a.time_taken is not None]
        avg_time = sum(times) / len(times) if times else 0
        accuracy = (correct / total * 100) if total > 0 else 0
        
        mastery_status = 'needs_practice'
        if total >= ProgressService.MIN_ATTEMPTS:
            accuracy_ratio = correct / total
            if accuracy_ratio >= ProgressService.MASTERY_THRESHOLD:
                mastery_status = 'mastered'
            elif accuracy_ratio >= ProgressService.LEARNING_THRESHOLD:
                mastery_status = 'learning'
        
        return {
            'description': description,
            'attempts': total,
            'correct': correct,
            'accuracy': accuracy,
            'avg_time': avg_time,
            'mastery_status': mastery_status
        }

    @staticmethod
    def analyze_level_problems(attempts: List[PracticeAttempt]) -> Dict:
        """Analyze problem patterns within a level"""
        problem_stats = {}
        
        for attempt in attempts:
            if attempt.problem not in problem_stats:
                problem_stats[attempt.problem] = {
                    'attempts': 0,
                    'correct': 0,
                    'total_time': 0,
                    'fastest_time': float('inf'),
                    'slowest_time': 0
                }
            
            stats = problem_stats[attempt.problem]
            stats['attempts'] += 1
            if attempt.is_correct:
                stats['correct'] += 1
            if attempt.time_taken:
                stats['total_time'] += attempt.time_taken
                stats['fastest_time'] = min(stats['fastest_time'], attempt.time_taken)
                stats['slowest_time'] = max(stats['slowest_time'], attempt.time_taken)
        
        # Calculate averages and percentages
        for problem, stats in problem_stats.items():
            stats['accuracy'] = (stats['correct'] / stats['attempts'] * 100)
            stats['avg_time'] = stats['total_time'] / stats['attempts']
            if stats['fastest_time'] == float('inf'):
                stats['fastest_time'] = 0
        
        return problem_stats

    @staticmethod
    def get_multiplication_table_stats(student_id: int) -> Dict:
        """Get detailed statistics for multiplication table progress"""
        attempts = PracticeAttempt.query.filter_by(
            user_id=student_id,
            operation='multiplication'
        ).all()

        # Initialize the multiplication table stats
        table_stats = {}
        for i in range(13):
            table_stats[i] = {}
            for j in range(13):
                table_stats[i][j] = {
                    'attempts': 0,
                    'correct': 0,
                    'accuracy': 0,
                    'average_time': 0
                }

        # Fill in the stats
        for i in range(1, 13):
            for j in range(1, 13):
                problem = f"{i} × {j}"
                relevant_attempts = [a for a in attempts if a.problem == problem]
                if relevant_attempts:
                    correct_count = sum(1 for a in relevant_attempts if a.is_correct)
                    table_stats[i][j] = {
                        'attempts': len(relevant_attempts),
                        'correct': correct_count,
                        'accuracy': (correct_count / len(relevant_attempts)) * 100,
                        'average_time': sum(a.time_taken for a in relevant_attempts if a.time_taken is not None) / sum(1 for a in relevant_attempts if a.time_taken is not None) if relevant_attempts else 0
                    }

        return table_stats

    @staticmethod
    def should_change_level(student_id: int, operation: str, current_level: int) -> Tuple[bool, int]:
        """Determine if a student should change levels based on recent performance"""
        recent_attempts = PracticeAttempt.query.filter_by(
            user_id=student_id,
            operation=operation,
            level=current_level
        ).order_by(PracticeAttempt.created_at.desc()).limit(10).all()

        if not recent_attempts:
            return False, current_level

        correct_count = sum(1 for a in recent_attempts if a.is_correct)
        success_rate = correct_count / len(recent_attempts)
        
        correct_times = [a.time_taken for a in recent_attempts if a.is_correct and a.time_taken]
        avg_time = sum(correct_times) / len(correct_times) if correct_times else float('inf')

        # Level up conditions
        if success_rate >= ProgressService.LEVEL_UP_ACCURACY and avg_time < ProgressService.LEVEL_UP_TIME:
            max_level = 5 if operation == 'addition' else 12
            return True, min(current_level + 1, max_level)
        
        # Level down conditions
        elif success_rate < ProgressService.LEVEL_DOWN_ACCURACY:
            return True, max(current_level - 1, 1)

        return False, current_level

    @staticmethod
    def analyze_missed_problems(student_id: int, operation: Optional[str] = None) -> List[Dict]:
        """Analyze commonly missed problems for a student"""
        query = PracticeAttempt.query.filter_by(user_id=student_id)
        if operation:
            query = query.filter_by(operation=operation)
        
        attempts = query.filter_by(is_correct=False).all()
        problem_counts = {}
        
        for attempt in attempts:
            key = (attempt.operation, attempt.problem)
            if key not in problem_counts:
                problem_counts[key] = {'count': 0, 'operation': attempt.operation, 'problem': attempt.problem}
            problem_counts[key]['count'] += 1
        
        return sorted(problem_counts.values(), key=lambda x: x['count'], reverse=True)
