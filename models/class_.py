from app import db
from datetime import datetime
from sqlalchemy import select
from models.user import User

# Association tables for many-to-many relationships
teacher_class = db.Table('teacher_class',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('is_primary', db.Boolean, default=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

student_class = db.Table('student_class',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Class(db.Model):
    __tablename__ = 'class'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    class_code = db.Column(db.String(7), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationships
    teachers = db.relationship('User',
                             secondary=teacher_class,
                             backref=db.backref('teaching_classes', lazy='dynamic'),
                             lazy='dynamic')
    
    students = db.relationship('User',
                             secondary=student_class,
                             backref=db.backref('enrolled_classes', lazy='dynamic'),
                             lazy='dynamic')
    
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.generate_class_code()
    
    def generate_class_code(self):
        """Generate a unique 7-character class code."""
        import random
        import string
        while True:
            # Generate a random 7-character code with uppercase letters and numbers
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            # Check if this code is already in use
            if not Class.query.filter_by(class_code=code).first():
                self.class_code = code
                break
    
    def add_teacher(self, teacher, is_primary=False):
        """Add a teacher to the class."""
        if not self.teachers.filter_by(id=teacher.id).first():
            db.session.execute(
                teacher_class.insert().values(
                    class_id=self.id,
                    teacher_id=teacher.id,
                    is_primary=is_primary
                )
            )
    
    def remove_teacher(self, teacher):
        """Remove a teacher from the class."""
        if self.teachers.filter_by(id=teacher.id).first():
            db.session.execute(
                teacher_class.delete().where(
                    (teacher_class.c.class_id == self.id) &
                    (teacher_class.c.teacher_id == teacher.id)
                )
            )
    
    def add_student(self, student):
        """Add a student to the class."""
        if not self.students.filter_by(id=student.id).first():
            db.session.execute(
                student_class.insert().values(
                    class_id=self.id,
                    student_id=student.id
                )
            )
    
    def remove_student(self, student):
        """Remove a student from the class."""
        if self.students.filter_by(id=student.id).first():
            db.session.execute(
                student_class.delete().where(
                    (student_class.c.class_id == self.id) &
                    (student_class.c.student_id == student.id)
                )
            )
    
    def get_primary_teacher(self):
        """Get the primary teacher for this class."""
        stmt = select(User).join(teacher_class).where(
            (teacher_class.c.class_id == self.id) &
            (teacher_class.c.is_primary == True)
        )
        result = db.session.execute(stmt).scalar()
        return result if result else self.teachers.first()
    
    def __repr__(self):
        return f'<Class {self.name}>'