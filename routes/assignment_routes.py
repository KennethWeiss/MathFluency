from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from models.class_ import Class, teacher_class
from datetime import datetime
from sqlalchemy import func, and_

# Create blueprint
assignment_bp = Blueprint('assignment', __name__)

# Teacher routes
@assignment_bp.route('/assignments')
@login_required
def list_assignments():
    """
    Display all assignments created by the current teacher.

    This route is accessible only to teachers. It fetches all assignments created by the current teacher and renders the teacher_list.html template.
    """
    # Check if user has teacher privileges
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get assignments created by this teacher
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
    return render_template('assignments/teacher_list.html', assignments=assignments, AssignmentProgress=AssignmentProgress)

@assignment_bp.route('/assignments/<int:id>')
@login_required
def view_assignment(id):
    """
    View details of a specific assignment.

    This route is accessible to both teachers and students. It fetches the assignment details and renders the view.html template.
    """
    # Get assignment or return 404 if not found
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher and not assignment.is_assigned_to_student(current_user):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('assignments/view.html', 
                        assignment=assignment,
                        func=func,
                        AssignmentProgress=AssignmentProgress)

@assignment_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        operation = request.form.get('operation')
        level = int(request.form.get('level'))
        required_problems = int(request.form.get('required_problems', 10))
        min_correct_percentage = int(request.form.get('min_correct_percentage', 80))
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        active = 'active' in request.form
        class_ids = request.form.getlist('class_ids')  # List of classes to assign to
        
        # Optional settings
        max_attempts = request.form.get('max_attempts_per_problem')
        show_solution_after = request.form.get('show_solution_after_attempts', 3)
        requires_work = request.form.get('requires_work_shown') == 'on'
        
        # Create assignment
        assignment = Assignment(
            title=title,
            description=description,
            operation=operation,
            level=level,
            required_problems=required_problems,
            min_correct_percentage=min_correct_percentage,
            due_date=due_date,
            active=active,
            teacher_id=current_user.id,
            max_attempts_per_problem=max_attempts,
            show_solution_after_attempts=show_solution_after,
            requires_work_shown=requires_work
        )
        
        db.session.add(assignment)
        
        # Add selected classes to assignment
        for class_id in class_ids:
            class_ = Class.query.get(class_id)
            if class_:
                assignment.classes.append(class_)
                # Initialize progress tracking for each student in the class
                for student in class_.students:
                    progress = AssignmentProgress(
                        student_id=student.id,
                        assignment_id=assignment.id
                    )
                    db.session.add(progress)
        
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('assignment.list_assignments'))
    
    # GET request - show create form
    # Get all classes where the current user is a teacher
    classes = Class.query.join(Class.teachers).filter(Class.teachers.contains(current_user)).all()
    return render_template('assignments/create.html', classes=classes)

@assignment_bp.route('/assignments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Update assignment fields
        assignment.title = request.form.get('title')
        assignment.description = request.form.get('description')
        assignment.operation = request.form.get('operation')
        assignment.level = int(request.form.get('level'))
        assignment.required_problems = int(request.form.get('required_problems', 10))
        assignment.min_correct_percentage = int(request.form.get('min_correct_percentage', 80))
        assignment.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
        
        # Optional settings
        assignment.max_attempts_per_problem = request.form.get('max_attempts_per_problem')
        assignment.show_solution_after_attempts = request.form.get('show_solution_after_attempts', 3)
        assignment.requires_work_shown = request.form.get('requires_work_shown') == 'on'
        
        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('assignment.list_assignments'))
    
    # GET request - display edit form
    classes = Class.query.join(Class.teachers).filter(Class.teachers.contains(current_user)).all()
    return render_template('assignments/edit.html', assignment=assignment, classes=classes)

@assignment_bp.route('/assignments/<int:id>/delete', methods=['POST'])
@login_required
def delete_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted successfully!', 'success')
    return redirect(url_for('assignment.list_assignments'))

@assignment_bp.route('/assignments/<int:id>/grade')
@login_required
def grade_assignment(id):
    """
    Display grading interface for teacher to review student work.

    This route is accessible only to teachers. It fetches the assignment details and renders the grade.html template.
    """
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    progress_entries = assignment.student_progress.all()
    return render_template('assignments/grade.html', assignment=assignment, progress_entries=progress_entries)

@assignment_bp.route('/assignments/<int:id>/grade/<int:student_id>', methods=['POST'])
@login_required
def submit_grade(id, student_id):
    """
    Submit or update a grade for a student's assignment.

    This route is accessible only to teachers. It updates the grade for the specified student and assignment.
    """
    # Verify permissions and assignment exists
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get student's progress record
    progress = AssignmentProgress.query.filter_by(
        assignment_id=id,
        student_id=student_id
    ).first_or_404()
    
    # Update grade and/or comment
    grade = request.form.get('grade')
    comment = request.form.get('comment')
    
    if grade:
        progress.override_grade(int(grade))
    if comment:
        progress.add_teacher_comment(comment)
    
    return jsonify({'success': True})

@assignment_bp.route('/assignment/<int:id>/info', methods=['GET'])
@login_required
def get_assignment_info(id):
    """
    Get basic information about an assignment in JSON format.

    This route returns the assignment ID, operation, level, and required problems in JSON format.
    """
    assignment = Assignment.query.get_or_404(id)
    return jsonify({
        'id': assignment.id,
        'operation': assignment.operation,
        'level': assignment.level,
        'required_problems': assignment.required_problems
    })

# Student routes
@assignment_bp.route('/student/assignments')
@login_required
def student_assignments():
    """
    Display all assignments assigned to the current student.

    This route is accessible only to students. It fetches all assignments assigned to the current student and renders the student_list.html template.
    """
    if current_user.is_teacher:
        return redirect(url_for('assignment.list_assignments'))
    
    # Get all assignments from classes the student is in
    assignments = Assignment.query\
        .join(Class, Assignment.classes.any(Class.id))\
        .join(Class.students)\
        .filter(Class.students.any(id=current_user.id))\
        .all()
    
    print("====================================")
    print(assignments)
    print(current_user.id)
    print("====================================")
    
    return render_template('assignments/student_list.html', assignments=assignments)


@assignment_bp.route('/assignments/<int:assignment_id>/student/<int:student_id>')
@login_required
def view_student_work(assignment_id, student_id):
    """
    View detailed work submitted by a specific student.

    This route is accessible only to teachers. It fetches the student's progress record and renders the student_work.html template.
    """
    # Verify permissions and assignment exists
    assignment = Assignment.query.get_or_404(assignment_id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get student's progress record
    progress = AssignmentProgress.query.filter_by(
        assignment_id=assignment_id,
        student_id=student_id
    ).first_or_404()
    
    attempts = AttemptHistory.query.filter_by(
        progress_id=progress.id
    ).order_by(AttemptHistory.created_at.desc()).all()
    
    return render_template('assignments/student_work.html',
                        assignment=assignment,
                        progress=progress,
                        attempts=attempts)

@assignment_bp.route('/assignments/<int:id>/start')
@login_required
def start_assignment(id):
    if current_user.is_teacher:
        return redirect(url_for('assignment.view_assignment', id=id))
    
    assignment = Assignment.query.get_or_404(id)
    if not assignment.is_assigned_to_student(current_user):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get or create progress entry
    progress = AssignmentProgress.query.filter_by(
        assignment_id=id,
        student_id=current_user.id
    ).first()
    
    if not progress:
        progress = AssignmentProgress(
            student_id=current_user.id,
            assignment_id=assignment.id
        )
        db.session.add(progress)
        db.session.commit()
    
    # Mark as started if not already
    if not progress.started:
        progress.started = True
        progress.start_time = datetime.utcnow()
        db.session.commit()
    
    return redirect(url_for('practice.practice', assignment_id=id))