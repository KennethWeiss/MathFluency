from datetime import datetime, timedelta
from database import db

class PracticeAttempt(db.Model):
    __tablename__ = 'practice_attempt'

    # Constants for mastery tracking
    MASTERY_THRESHOLD = 0.8  # 80% accuracy for mastery
    MIN_ATTEMPTS = 3  # Minimum attempts before considering mastery
    LEARNING_THRESHOLD = 0.6  # 60% accuracy for learning status

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation = db.Column(db.String(20), nullable=False)  # 'addition' or 'multiplication'
    level = db.Column(db.Integer, nullable=False)
    problem = db.Column(db.String(50), nullable=False)  # Full problem string (e.g., "5 × 8")
    user_answer = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationship to User
    user = db.relationship('User', backref=db.backref('practice_attempts', lazy=True))

    @classmethod
    def get_mastery_status(cls, db_session, user_id, operation, level):
        """Get the mastery status for problems at this level."""
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get all attempts for this level in the past week
        attempts = db_session.query(cls).filter(
            cls.user_id == user_id,
            cls.operation == operation,
            cls.level == level,
            cls.created_at >= week_ago
        ).all()
        
        if not attempts or len(attempts) < cls.MIN_ATTEMPTS:
            return 'needs_practice'
            
        # Calculate accuracy
        correct = sum(1 for a in attempts if a.is_correct)
        accuracy = correct / len(attempts)
        
        # Determine mastery level
        if accuracy >= cls.MASTERY_THRESHOLD:
            return 'mastered'
        elif accuracy >= cls.LEARNING_THRESHOLD:
            return 'learning'
        
        return 'needs_practice'

    def __repr__(self):
        return f'<PracticeAttempt {self.problem} by User {self.user_id}>'