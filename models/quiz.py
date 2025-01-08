# models/quiz.py
from app import db
from datetime import datetime
from models.user import User

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation = db.Column(db.String(20), nullable=False)  # multiplication, addition, etc.
    adaptive = db.Column(db.Boolean, default=False)
    duration = db.Column(db.Integer, nullable=False)  # in seconds
    status = db.Column(db.String(20), default='waiting')  # waiting, active, finished
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', backref='quizzes')
    participants = db.relationship('QuizParticipant', backref='quiz', lazy=True)
    questions = db.relationship('QuizQuestion', backref='quiz')

class QuizParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('QuizAnswer', backref='participant')
    
    # Relationships
    user = db.relationship('User', backref='quiz_participations')

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    problem = db.Column(db.String(100))
    answer = db.Column(db.Integer)
    level = db.Column(db.Integer)

class QuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('quiz_participant.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'))
    answer = db.Column(db.Integer)
    correct = db.Column(db.Boolean)
    time_taken = db.Column(db.Float)  # time taken in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)