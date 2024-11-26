from app import db
from datetime import datetime

class PracticeAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation = db.Column(db.String(20), nullable=False)  # 'addition' or 'multiplication'
    level = db.Column(db.Integer, nullable=False)
    problem = db.Column(db.String(50), nullable=False)
    user_answer = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('practice_attempts', lazy=True))