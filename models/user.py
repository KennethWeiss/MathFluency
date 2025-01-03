from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256))
    is_teacher = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Google OAuth fields
    google_id = db.Column(db.String(256), nullable=True, unique=True)
    avatar_url = db.Column(db.String(256), nullable=True)
    
    # Note: relationships are defined via backref in the Class model
    # taught_classes - classes where user is a teacher
    # enrolled_classes - classes where user is a student

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    @property
    def is_student(self):
        return not self.is_teacher and not self.is_admin

    @property
    def full_name(self):
        return self.username  # You can modify this if you add first_name/last_name fields

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_teacher': self.is_teacher,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'avatar_url': self.avatar_url
        }
        
    def get_primary_classes(self):
        """Get classes where this user is the primary teacher"""
        if not self.is_teacher:
            return []
        from models.class_ import teacher_class
        return db.session.execute(
            db.select(Class).
            join(teacher_class).
            where(teacher_class.c.teacher_id == self.id).
            where(teacher_class.c.is_primary == True)
        ).scalars().all()
