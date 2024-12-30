from models.practice_attempt import PracticeAttempt
from typing import Dict, List, Optional

class ProgressService:
    @staticmethod
    def get_student_stats(student_id: int, operation: Optional[str] = None) -> Dict:
        """Calculate statistics for a student's practice attempts"""
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
        correct_times = [a.time_taken for a in attempts if a.is_correct]
        avg_time = sum(correct_times) / len(correct_times) if correct_times else 0
        fastest_time = min(correct_times) if correct_times else 0
        
        # Calculate level stats
        levels = {}
        for attempt in attempts:
            level = attempt.level
            if level not in levels:
                levels[level] = {
                    'total': 0,
                    'correct': 0,
                    'times': []
                }
            levels[level]['total'] += 1
            if attempt.is_correct:
                levels[level]['correct'] += 1
                levels[level]['times'].append(attempt.time_taken)
        
        # Format level stats
        level_stats = {}
        for level, data in levels.items():
            level_stats[level] = {
                'accuracy': (data['correct'] / data['total'] * 100),
                'avg_time': sum(data['times']) / len(data['times']) if data['times'] else 0,
                'attempts': data['total']
            }
        
        return {
            'total_attempts': total_attempts,
            'accuracy': accuracy,
            'current_streak': current_streak,
            'average_time': avg_time,
            'fastest_time': fastest_time,
            'levels': level_stats
        }

    @staticmethod
    def analyze_level(operation: str, level: int) -> Dict:
        """Analyze performance for a specific operation and level"""
        attempts = PracticeAttempt.query.filter_by(
            operation=operation,
            level=level
        ).all()
        
        if not attempts:
            return {'problems': [], 'accuracy': 0, 'avg_time': 0}
        
        problems = {}
        for attempt in attempts:
            key = f"{attempt.num1} {attempt.operation} {attempt.num2}"
            if key not in problems:
                problems[key] = {'total': 0, 'correct': 0, 'times': []}
            problems[key]['total'] += 1
            if attempt.is_correct:
                problems[key]['correct'] += 1
                problems[key]['times'].append(attempt.time_taken)
        
        problem_stats = []
        for problem, stats in problems.items():
            problem_stats.append({
                'problem': problem,
                'accuracy': (stats['correct'] / stats['total'] * 100),
                'avg_time': sum(stats['times']) / len(stats['times']) if stats['times'] else 0,
                'attempts': stats['total']
            })
        
        return {
            'problems': sorted(problem_stats, key=lambda x: x['accuracy']),
            'accuracy': sum(p['accuracy'] for p in problem_stats) / len(problem_stats),
            'avg_time': sum(p['avg_time'] for p in problem_stats) / len(problem_stats)
        }
