from app import db
from datetime import datetime
import random
import string

# Association table for teachers and classes
teacher_class = db.Table('teacher_class',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('is_primary', db.Boolean, default=False),  # To mark the primary teacher
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Association table for students and classes
student_class = db.Table('student_class',
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    class_code = db.Column(db.String(8), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teachers = db.relationship('User',
                             secondary=teacher_class,
                             backref=db.backref('taught_classes', lazy='dynamic'),
                             lazy='dynamic')
    
    students = db.relationship('User',
                             secondary=student_class,
                             backref=db.backref('enrolled_classes', lazy='dynamic'),
                             lazy='dynamic')

    def __repr__(self):
        return f'<Class {self.name}>'

    @staticmethod
    def generate_class_code(length=6):
        """Generate a random class code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(length))
            if not Class.query.filter_by(class_code=code).first():
                return code

    def add_teacher(self, teacher, is_primary=False):
        """Add a teacher to the class"""
        if not teacher.is_teacher:
            raise ValueError("User must be a teacher")
        
        # If this is the primary teacher, remove primary status from others
        if is_primary:
            for t in self.teachers:
                db.session.execute(
                    teacher_class.update().
                    where(teacher_class.c.class_id == self.id).
                    where(teacher_class.c.teacher_id == t.id).
                    values(is_primary=False)
                )
        
        # Add the new teacher
        db.session.execute(
            teacher_class.insert().values(
                class_id=self.id,
                teacher_id=teacher.id,
                is_primary=is_primary
            )
        )
        db.session.commit()

    def add_student(self, student):
        """Add a student to the class"""
        if student.is_teacher:
            raise ValueError("Teachers cannot be enrolled as students")
        self.students.append(student)
        db.session.commit()

    def remove_student(self, student):
        """Remove a student from the class"""
        self.students.remove(student)
        db.session.commit()

    def get_primary_teacher(self):
        """Get the primary teacher for this class"""
        result = db.session.execute(
            db.select(User).
            join(teacher_class).
            where(teacher_class.c.class_id == self.id).
            where(teacher_class.c.is_primary == True)
        ).first()
        return result[0] if result else None