from flask_login import UserMixin
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(64), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(db.String(120), nullable=False, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(db.String(256))
    is_teacher: Mapped[bool] = mapped_column(db.Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(db.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    # Google OAuth fields
    google_id: Mapped[Optional[str]] = mapped_column(db.String(256), nullable=True, unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(db.String(256), nullable=True)
    
    # User name fields
    first_name: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)
    
    # Note: relationships are defined via backref in the Class model
    # teacher_classes - classes where user is a teacher
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
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
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
            
        # Use teaching_classes relationship directly
        return self.teaching_classes.all()
