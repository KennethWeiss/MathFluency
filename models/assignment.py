from app import db
from datetime import datetime
import json

# Association tables
student_assignments = db.Table('student_assignments',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('assignment_id', db.Integer, db.ForeignKey('assignment.id'), primary_key=True)
)

prerequisite_assignments = db.Table('prerequisite_assignments',
    db.Column('assignment_id', db.Integer, db.ForeignKey('assignment.id'), primary_key=True),
    db.Column('prerequisite_id', db.Integer, db.ForeignKey('assignment.id'), primary_key=True)
)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    
    # Assignment settings
    operation = db.Column(db.String(20), nullable=False)  # 'addition' or 'multiplication'
    level = db.Column(db.Integer, nullable=False)
    required_problems = db.Column(db.Integer, default=10)
    min_correct_percentage = db.Column(db.Integer, default=80)
    active = db.Column(db.Boolean, default=True)  # Whether the assignment is visible to students

    # Custom multiplication settings
    custom_number1 = db.Column(db.Integer)
    custom_number2 = db.Column(db.Integer)
    
    # Enhanced settings
    max_attempts_per_problem = db.Column(db.Integer, default=None)  # None means unlimited
    show_solution_after_attempts = db.Column(db.Integer, default=3)
    requires_work_shown = db.Column(db.Boolean, default=False)
    is_template = db.Column(db.Boolean, default=False)  # Can be saved as template
    partial_credit = db.Column(db.Boolean, default=True)
    late_submission_policy = db.Column(db.String(20), default='no_credit')  # no_credit, partial_credit, full_credit
    visibility = db.Column(db.String(20), default='immediate')  # immediate, date, prerequisite
    practice_mode_enabled = db.Column(db.Boolean, default=True)
    
    # Help resources
    hint_system = db.Column(db.JSON)  # Store multiple levels of hints
    video_tutorial_url = db.Column(db.String(500))
    
    # Assignment metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    available_from = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime, nullable=False)
    is_graded = db.Column(db.Boolean, default=False)
    graded_at = db.Column(db.DateTime)
    
    # Assignment type flags
    is_class_assignment = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)
    
    # Relationships
    teacher = db.relationship('User', backref='created_assignments', foreign_keys=[teacher_id])
    assigned_class = db.relationship('Class', backref='assignments')
    individual_students = db.relationship('User', secondary=student_assignments, backref='individual_assignments')
    student_progress = db.relationship('AssignmentProgress', backref='assignment', lazy='dynamic')
    prerequisites = db.relationship(
        'Assignment', secondary=prerequisite_assignments,
        primaryjoin=(prerequisite_assignments.c.assignment_id == id),
        secondaryjoin=(prerequisite_assignments.c.prerequisite_id == id),
        backref='required_for'
    )

    def get_progress(self, student):
        """Get or create progress entry for a student."""
        progress = AssignmentProgress.query.filter_by(
            assignment_id=self.id,
            student_id=student.id
        ).first()
        
        if not progress:
            progress = AssignmentProgress(
                assignment_id=self.id,
                student_id=student.id
            )
            db.session.add(progress)
            db.session.commit()
        
        return progress
    
    def get_assigned_students(self):
        """Get all students assigned to this assignment (class or individual)."""
        if self.is_class_assignment and self.assigned_class:
            return self.assigned_class.students.all()
        return self.individual_students
    
    def is_assigned_to_student(self, student):
        """Check if a student is assigned this assignment."""
        if self.is_class_assignment:
            return student.class_id == self.class_id
        return student in self.individual_students
    
    def mark_as_graded(self):
        """Mark the assignment as graded."""
        self.is_graded = True
        self.graded_at = datetime.utcnow()
        db.session.commit()
    
    def is_overdue(self):
        """Check if assignment is past due date."""
        return datetime.utcnow() > self.due_date
    
    def is_available(self):
        """Check if assignment is available to start."""
        now = datetime.utcnow()
        if self.available_from and now < self.available_from:
            return False
        return True
    
    def prerequisites_completed(self, student):
        """Check if student has completed all prerequisites."""
        for prereq in self.prerequisites:
            progress = AssignmentProgress.query.filter_by(
                student_id=student.id,
                assignment_id=prereq.id
            ).first()
            if not progress or not progress.completed:
                return False
        return True
    
    def can_start(self, student):
        """Check if student can start this assignment."""
        if not self.is_available():
            return False
        if self.visibility == 'prerequisite' and not self.prerequisites_completed(student):
            return False
        return True
    
    def needs_review(self):
        """Check if assignment needs teacher review."""
        completed_progress = self.student_progress.filter_by(completed=True).all()
        if not self.is_graded:
            return any(completed_progress)
        return any(p.completed_at > self.graded_at for p in completed_progress if p.completed_at)

class AttemptHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    progress_id = db.Column(db.Integer, db.ForeignKey('assignment_progress.id'), nullable=False)
    problem = db.Column(db.String(100))  # Store the problem text
    student_answer = db.Column(db.String(100))
    correct_answer = db.Column(db.String(100))
    is_correct = db.Column(db.Boolean, nullable=False)
    work_shown = db.Column(db.Text)  # Student's work if required
    hints_used = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer)  # Time spent in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    progress = db.relationship('AssignmentProgress', backref='attempts')

class AssignmentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    
    # Progress tracking
    problems_attempted = db.Column(db.Integer, default=0)
    problems_correct = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    # Enhanced tracking
    total_time_spent = db.Column(db.Integer, default=0)  # Total time in seconds
    streak_count = db.Column(db.Integer, default=0)  # Consecutive correct answers
    mastery_level = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    last_attempt_at = db.Column(db.DateTime)
    practice_mode = db.Column(db.Boolean, default=False)
    student_notes = db.Column(db.Text)
    
    # Grading
    teacher_comment = db.Column(db.String(500))
    grade_override = db.Column(db.Integer)

    @property
    def score(self):
        """Calculate the percentage score for this assignment."""
        if self.problems_attempted == 0:
            return 0
        if self.grade_override is not None:
            return self.grade_override
        return round((self.problems_correct / self.problems_attempted) * 100)
    
    # Status flags
    needs_review = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('User', backref='assignment_progress')
    
    def calculate_score(self):
        """Calculate the percentage score for this assignment."""
        if self.grade_override is not None:
            return self.grade_override
        if self.problems_attempted == 0:
            return 0
            
        # Handle partial credit if enabled
        if self.assignment.partial_credit:
            return (self.problems_correct / self.assignment.required_problems) * 100
        return (self.problems_correct / self.problems_attempted) * 100
    
    def update_mastery_level(self):
        """Update mastery level based on performance."""
        recent_attempts = AttemptHistory.query.filter_by(progress_id=self.id)\
            .order_by(AttemptHistory.created_at.desc())\
            .limit(10).all()
            
        if not recent_attempts:
            return
            
        # Calculate mastery based on recent performance and time spent
        correct_rate = sum(1 for a in recent_attempts if a.is_correct) / len(recent_attempts)
        avg_time = sum(a.time_spent for a in recent_attempts) / len(recent_attempts)
        
        # Adjust mastery based on multiple factors
        self.mastery_level = correct_rate * (1 - min(avg_time / 120, 0.5))  # Cap time penalty at 50%
        db.session.commit()
    
    def update_progress(self, problem, student_answer, correct_answer, is_correct, 
                       work_shown=None, hints_used=0, time_spent=0):
        """Update progress after a problem attempt."""
        # Record attempt
        attempt = AttemptHistory(
            progress_id=self.id,
            problem=problem,
            student_answer=student_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            work_shown=work_shown,
            hints_used=hints_used,
            time_spent=time_spent
        )
        db.session.add(attempt)
        
        # Update progress
        self.problems_attempted += 1
        self.total_time_spent += time_spent
        self.last_attempt_at = datetime.utcnow()
        
        if is_correct:
            self.problems_correct += 1
            self.streak_count += 1
        else:
            self.streak_count = 0
        
        # Check completion
        assignment = self.assignment
        if (self.problems_attempted >= assignment.required_problems and 
            self.calculate_score() >= assignment.min_correct_percentage):
            self.completed = True
            self.completed_at = datetime.utcnow()
            
            # If assignment was already graded, mark for review
            if assignment.is_graded:
                self.needs_review = True
        
        # Update mastery level
        self.update_mastery_level()
        db.session.commit()
    
    def add_teacher_comment(self, comment):
        """Add teacher feedback."""
        self.teacher_comment = comment
        db.session.commit()
    
    def override_grade(self, grade):
        """Allow teacher to override the calculated grade."""
        self.grade_override = grade
        db.session.commit()
    
    def add_note(self, note):
        """Add student note."""
        self.student_notes = note
        db.session.commit()
    
    def get_analytics(self):
        """Get detailed analytics for this student's progress."""
        attempts = self.attempts
        if not attempts:
            return None
            
        return {
            'total_time': self.total_time_spent,
            'average_time_per_problem': self.total_time_spent / len(attempts),
            'success_rate': self.problems_correct / self.problems_attempted,
            'mastery_level': self.mastery_level,
            'highest_streak': max(self.streak_count, 
                                max((a.streak_count for a in attempts), default=0)),
            'hints_usage': sum(a.hints_used for a in attempts) / len(attempts),
            'completion_rate': self.problems_attempted / self.assignment.required_problems
        }