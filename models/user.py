from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime
from models.class_ import Class

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_teacher = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Student-specific fields
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    
    # Teacher-specific relationships
    students = db.relationship('User', 
                             backref=db.backref('teacher', remote_side=[id]),
                             foreign_keys=[teacher_id],
                             lazy='dynamic')
    classes = db.relationship('Class', 
                            backref='teacher',
                            foreign_keys=[Class.teacher_id],
                            lazy='dynamic')
    
    # Student's class relationship
    enrolled_class = db.relationship('Class',
                                   foreign_keys=[class_id],
                                   backref=db.backref('students', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def make_teacher(self):
        self.is_teacher = True
        db.session.commit()
    
    def make_student(self):
        self.is_teacher = False
        db.session.commit()
    
    def assign_to_class(self, class_obj):
        if not self.is_teacher:
            self.class_id = class_obj.id
            self.teacher_id = class_obj.teacher_id
            db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'
