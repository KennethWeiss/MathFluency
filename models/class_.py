from app import db
from datetime import datetime
import random
import string

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    class_code = db.Column(db.String(8), nullable=True)  # Temporarily nullable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('class_code', name='uq_class_code'),
    )
    
    def __repr__(self):
        return f'<Class {self.name}>'
    
    @staticmethod
    def generate_class_code():
        """Generate a unique 7-character class code."""
        while True:
            # Generate a code: 7 characters, mix of uppercase letters and numbers
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            # Check if this code already exists
            if not Class.query.filter_by(class_code=code).first():
                return code