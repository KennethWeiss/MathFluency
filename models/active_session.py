from datetime import datetime, timedelta
from app import db

class ActiveSession(db.Model):
    __tablename__ = 'active_session'

    # Constants
    INACTIVE_THRESHOLD = 15  # Minutes until a session is considered inactive

    # Columns
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50))  # 'practice', 'assignment', etc.
    details = db.Column(db.String(255))  # Current problem, level, etc.
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationship to User
    user = db.relationship('User', backref=db.backref('active_session', uselist=False))

    def __repr__(self):
        """String representation of the active session."""
        return f'<ActiveSession {self.user.username}: {self.activity_type}>'

    @classmethod
    def cleanup_inactive(cls, db_session):
        """Remove sessions that have been inactive for too long."""
        cutoff = datetime.utcnow() - timedelta(minutes=cls.INACTIVE_THRESHOLD)
        inactive = cls.query.filter(cls.last_active < cutoff).all()
        for session in inactive:
            db_session.delete(session)
        db_session.commit()