from app import db
from datetime import datetime
from models.class_ import Class

class Assignment(db.Model):
    __tablename__ = 'assignment'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    operation = db.Column(db.String(20), nullable=False)  # add, subtract, multiply, divide
    level = db.Column(db.Integer, nullable=False)  # 1-5 for difficulty
    required_problems = db.Column(db.Integer, default=10)
    min_correct_percentage = db.Column(db.Integer, default=80)
    due_date = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Teacher who created the assignment
    teacher_id = db.Column(db.Integer, 
                          db.ForeignKey('user.id', name='fk_assignment_teacher_id'),
                          nullable=False)
    teacher = db.relationship('User', backref='created_assignments')
    
    # Optional settings
    max_attempts_per_problem = db.Column(db.Integer)  # None means unlimited
    show_solution_after_attempts = db.Column(db.Integer, default=3)
    requires_work_shown = db.Column(db.Boolean, default=False)
    
    # Many-to-many relationship with classes
    classes = db.relationship('Class',
                            secondary='assignment_class',
                            backref=db.backref('assignments', lazy='dynamic'),
                            lazy='dynamic')
    
    # One-to-many relationship with progress entries
    student_progress = db.relationship('AssignmentProgress',
                                     back_populates='assignment',
                                     lazy='dynamic')
    
    def __init__(self, title, description, operation, level, required_problems=10,
                 min_correct_percentage=80, due_date=None, active=True, teacher_id=None,
                 class_id=None, max_attempts_per_problem=None,
                 show_solution_after_attempts=3, requires_work_shown=False):
        self.title = title
        self.description = description
        self.operation = operation
        self.level = level
        self.required_problems = required_problems
        self.min_correct_percentage = min_correct_percentage
        self.due_date = due_date
        self.active = active
        self.teacher_id = teacher_id
        self.max_attempts_per_problem = max_attempts_per_problem
        self.show_solution_after_attempts = show_solution_after_attempts
        self.requires_work_shown = requires_work_shown
        
        # Add to class if specified
        if class_id:
            class_ = Class.query.get(class_id)
            if class_:
                self.classes.append(class_)
    
    def is_assigned_to_student(self, student):
        """Check if this assignment is assigned to the given student"""
        return any(student in class_.students.all() for class_ in self.classes.all())
    
    def get_progress(self, student_id):
        """Get the progress for a specific student"""
        return AssignmentProgress.query.filter_by(
            assignment_id=self.id,
            student_id=student_id
        ).first()
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

# Association table for assignments and classes
assignment_class = db.Table('assignment_class',
    db.Column('assignment_id', db.Integer, 
              db.ForeignKey('assignment.id', name='fk_assignment_class_assignment_id'),
              primary_key=True),
    db.Column('class_id', db.Integer, 
              db.ForeignKey('class.id', name='fk_assignment_class_class_id'),
              primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class AssignmentProgress(db.Model):
    """Tracks a student's progress on an assignment"""
    __tablename__ = 'assignment_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, 
                          db.ForeignKey('user.id', name='fk_assignment_progress_student_id'),
                          nullable=False)
    assignment_id = db.Column(db.Integer, 
                            db.ForeignKey('assignment.id', name='fk_assignment_progress_assignment_id'),
                            nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    problems_completed = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_attempts = db.Column(db.Integer, default=0)
    
    # Relationships
    student = db.relationship('User', backref='assignment_progress')
    assignment = db.relationship('Assignment', back_populates='student_progress')
    attempts = db.relationship('AttemptHistory', backref='progress', lazy='dynamic')
    
    def __init__(self, student_id, assignment_id):
        self.student_id = student_id
        self.assignment_id = assignment_id
    
    @property
    def accuracy(self):
        """Calculate the accuracy percentage"""
        if self.problems_completed == 0:
            return 0
        return round((self.correct_answers / self.problems_completed) * 100)
    
    @property
    def status(self):
        """Get the current status of the assignment progress"""
        if not self.started_at:
            return 'Not Started'
        if self.completed_at:
            return 'Completed'
        return 'In Progress'
    
    def __repr__(self):
        return f'<AssignmentProgress student={self.student_id} assignment={self.assignment_id}>'

class AttemptHistory(db.Model):
    """Records each attempt a student makes on a problem"""
    __tablename__ = 'attempt_history'
    
    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, 
                           db.ForeignKey('assignment_progress.id', name='fk_attempt_history_progress_id'),
                           nullable=False)
    problem_number = db.Column(db.Integer, nullable=False)
    student_answer = db.Column(db.String(50), nullable=False)
    correct_answer = db.Column(db.String(50), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    work_shown = db.Column(db.Text)  # Student's work/explanation if required
    attempt_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AttemptHistory progress={self.progress_id} problem={self.problem_number}>'