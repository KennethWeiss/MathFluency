from datetime import datetime, timedelta
from database import db
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class PracticeAttempt(db.Model):
    __tablename__ = 'practice_attempt'

    # Constants for mastery tracking
    MASTERY_THRESHOLD = 0.8  # 80% accuracy for mastery
    MIN_ATTEMPTS = 3  # Minimum attempts before considering mastery
    LEARNING_THRESHOLD = 0.6  # 60% accuracy for learning status

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    operation: Mapped[str] = mapped_column(db.String(20), nullable=False)
    level: Mapped[int] = mapped_column(nullable=False)
    problem: Mapped[str] = mapped_column(db.String(50), nullable=False)
    user_answer: Mapped[int] = mapped_column(nullable=False)
    correct_answer: Mapped[int] = mapped_column(nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    time_taken: Mapped[Optional[float]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Define relationship to User
    user: Mapped["User"] = relationship(back_populates="practice_attempts")

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