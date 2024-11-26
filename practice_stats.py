from app import app, db
from models.practice_attempt import PracticeAttempt
from sqlalchemy import func

with app.app_context():
    # Get total attempts
    total_attempts = PracticeAttempt.query.count()
    
    # Get correct attempts and calculate accuracy
    correct_attempts = PracticeAttempt.query.filter_by(is_correct=True).count()
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Get average time taken
    avg_time = db.session.query(func.avg(PracticeAttempt.time_taken)).scalar() or 0
    
    # Get fastest correct attempt
    fastest_correct = PracticeAttempt.query.filter_by(is_correct=True)\
        .order_by(PracticeAttempt.time_taken.asc()).first()
    
    # Get streak (consecutive correct answers)
    attempts = PracticeAttempt.query.order_by(PracticeAttempt.created_at.desc()).all()
    current_streak = 0
    for attempt in attempts:
        if attempt.is_correct:
            current_streak += 1
        else:
            break
    
    print("\n📊 Practice Session Statistics 📊\n")
    print(f"Total Attempts: {total_attempts}")
    print(f"Correct Answers: {correct_attempts}")
    print(f"Accuracy Rate: {accuracy:.1f}%")
    print(f"Average Time per Problem: {avg_time:.1f} seconds")
    if fastest_correct:
        print(f"Fastest Correct Solution: {fastest_correct.problem} in {fastest_correct.time_taken:.1f} seconds")
    print(f"Current Streak: {current_streak} correct in a row")
    
    # Show operation-specific stats
    print("\n🔢 Stats by Operation:")
    operations = db.session.query(PracticeAttempt.operation).distinct().all()
    for (operation,) in operations:
        op_attempts = PracticeAttempt.query.filter_by(operation=operation)
        total_op = op_attempts.count()
        correct_op = op_attempts.filter_by(is_correct=True).count()
        avg_time_op = db.session.query(func.avg(PracticeAttempt.time_taken))\
            .filter(PracticeAttempt.operation == operation).scalar() or 0
        
        print(f"\n{operation.title()}:")
        print(f"  Total Attempts: {total_op}")
        print(f"  Accuracy: {(correct_op/total_op*100):.1f}%")
        print(f"  Average Time: {avg_time_op:.1f} seconds")
