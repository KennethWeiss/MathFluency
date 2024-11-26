from datetime import datetime
from app import db

# Association table for standard prerequisites
standard_prerequisites = db.Table('standard_prerequisites',
    db.Column('standard_id', db.Integer, db.ForeignKey('standard.id'), primary_key=True),
    db.Column('prerequisite_id', db.Integer, db.ForeignKey('standard.id'), primary_key=True)
)

class Standard(db.Model):
    __tablename__ = 'standard'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    domain = db.Column(db.String(50), nullable=False)
    cluster = db.Column(db.String(200))
    problems = db.relationship('Problem', secondary='problem_standards', back_populates='standards')
    prerequisites = db.relationship(
        'Standard',
        secondary=standard_prerequisites,
        primaryjoin=(id == standard_prerequisites.c.standard_id),
        secondaryjoin=(id == standard_prerequisites.c.prerequisite_id),
        backref=db.backref('dependent_standards', lazy='dynamic'),
        lazy='dynamic'
    )
    substandards = db.relationship('SubStandard', back_populates='standard', lazy=True, order_by='SubStandard.level')

    @property
    def current_mastery_level(self):
        """Calculate overall mastery level based on substandards"""
        substandards = self.substandards
        if not substandards:
            return None
        
        # Get the lowest substandard level that hasn't been mastered
        for sub in sorted(substandards, key=lambda x: x.level):
            # Consider a substandard mastered if student has >= 80% success rate
            progress = StudentSubStandardProgress.query.filter_by(
                substandard_id=sub.id
            ).first()
            
            if not progress or (progress.total_attempts > 0 and 
                              (progress.correct_attempts / progress.total_attempts) < 0.8):
                return sub.level - 1  # Return previous level
        
        return len(substandards)  # All levels mastered

class SubStandard(db.Model):
    __tablename__ = 'substandard'
    id = db.Column(db.Integer, primary_key=True)
    standard_id = db.Column(db.Integer, db.ForeignKey('standard.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1-4 for rubric levels
    examples = db.Column(db.Text)  # Optional examples for this level
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to parent standard
    standard = db.relationship('Standard', back_populates='substandards', lazy=True)

class StudentSubStandardProgress(db.Model):
    __tablename__ = 'student_substandard_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    substandard_id = db.Column(db.Integer, db.ForeignKey('substandard.id'), nullable=False)
    total_attempts = db.Column(db.Integer, default=0)
    correct_attempts = db.Column(db.Integer, default=0)
    mastery_level = db.Column(db.Float, default=0.0)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('substandard_progress', lazy=True))
    substandard = db.relationship('SubStandard', backref=db.backref('student_progress', lazy=True))

class StudentStandardProgress(db.Model):
    __tablename__ = 'student_standard_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    standard_id = db.Column(db.Integer, db.ForeignKey('standard.id'), nullable=False)
    total_attempts = db.Column(db.Integer, default=0)
    correct_attempts = db.Column(db.Integer, default=0)
    mastery_level = db.Column(db.Float, default=0.0)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('standard_progress', lazy=True))
    standard = db.relationship('Standard', backref=db.backref('student_progress', lazy=True))
