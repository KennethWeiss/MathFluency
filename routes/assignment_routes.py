from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models.assignment import Assignment, AssignmentProgress, AttemptHistory
from models.class_ import Class
from datetime import datetime
from sqlalchemy import func

# Create blueprint
assignment_bp = Blueprint('assignment', __name__)

# Teacher routes
@assignment_bp.route('/assignments')
@login_required
def list_assignments():
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.index'))
    
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()
    return render_template('assignments/teacher_list.html', assignments=assignments)

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
        class_id = request.form.get('class_id')
        
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
            class_id=class_id,
            max_attempts_per_problem=max_attempts,
            show_solution_after_attempts=show_solution_after,
            requires_work_shown=requires_work
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        # Create progress entries for all students in the class
        if class_id:
            class_ = Class.query.get(class_id)
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
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('assignments/create.html', classes=classes)

@assignment_bp.route('/assignments/<int:id>')
@login_required
def view_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher and not assignment.is_assigned_to_student(current_user):
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('assignments/view.html', assignment=assignment, func=func, AssignmentProgress = AssignmentProgress)

@assignment_bp.route('/assignments/<int:id>/grade')
@login_required
def grade_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    progress_entries = assignment.student_progress.all()
    return render_template('assignments/grade.html', assignment=assignment, progress_entries=progress_entries)



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
    
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
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

@assignment_bp.route('/assignments/<int:id>/grade/<int:student_id>', methods=['POST'])
@login_required
def submit_grade(id, student_id):
    assignment = Assignment.query.get_or_404(id)
    if not current_user.is_teacher or assignment.teacher_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    progress = AssignmentProgress.query.filter_by(
        assignment_id=id,
        student_id=student_id
    ).first_or_404()
    
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
    if current_user.is_teacher:
        return redirect(url_for('assignment.list_assignments'))
    
    # Get all assignments from classes the student is in
    assignments = Assignment.query\
        .join(Class, Assignment.class_id == Class.id)\
        .join(Class.students)\
        .filter(Class.students.any(id=current_user.id))\
        .all()
    
    return render_template('assignments/student_list.html', assignments=assignments)

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
            assignment_id=id,
            student_id=current_user.id
        )
        db.session.add(progress)
        db.session.commit()
    
    # Mark as started if not already
    if not progress.started:
        progress.started = True
        progress.start_time = datetime.utcnow()
        db.session.commit()
    
    return redirect(url_for('practice.practice', assignment_id=id))