from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.class_ import Class
from models.user import User
from app import db

class_bp = Blueprint('class', __name__)

@class_bp.route('/classes')
@login_required
def list_classes():
    if current_user.is_teacher:
        classes = current_user.teaching_classes.all()
    else:
        classes = current_user.enrolled_classes.all()
    return render_template('classes/list.html', classes=classes)

@class_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
def create_class():
    if not current_user.is_teacher:
        flash('Only teachers can create classes.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Class name is required.', 'danger')
            return render_template('classes/create.html')
        
        class_ = Class(
            name=name,
            description=description,
            class_code=Class.generate_class_code()
        )
        
        db.session.add(class_)
        class_.add_teacher(current_user, is_primary=True)
        db.session.commit()
        
        flash('Class created successfully!', 'success')
        return redirect(url_for('class.view_class', id=class_.id))
    
    return render_template('classes/create.html')

@class_bp.route('/classes/<int:id>')
@login_required
def view_class(id):
    class_ = Class.query.get_or_404(id)
    
    # Check if user has access to this class
    if current_user.is_teacher and current_user not in class_.teachers:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    elif not current_user.is_teacher and current_user not in class_.students:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student_count = class_.students.count()
    primary_teacher = class_.get_primary_teacher()
    
    return render_template('classes/view.html', 
                         class_=class_, 
                         student_count=student_count,
                         primary_teacher=primary_teacher)

@class_bp.route('/classes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or current_user not in class_.teachers:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Class name is required.', 'danger')
            return render_template('classes/edit.html', class_=class_)
        
        class_.name = name
        class_.description = description
        db.session.commit()
        
        flash('Class updated successfully!', 'success')
        return redirect(url_for('class.view_class', id=class_.id))
    
    return render_template('classes/edit.html', class_=class_)

@class_bp.route('/classes/<int:id>/students')
@login_required
def manage_students(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or current_user not in class_.teachers:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all non-teacher users who aren't in this class
    available_students = User.query.filter_by(is_teacher=False)\
                                 .filter(~User.enrolled_classes.any(Class.id == id))\
                                 .all()
    
    return render_template('classes/manage_students.html', 
                         class_=class_,
                         available_students=available_students)

@class_bp.route('/classes/<int:id>/add_student', methods=['POST'])
@login_required
def add_student(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or current_user not in class_.teachers:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student_id = request.form.get('student_id')
    if not student_id:
        flash('Student ID is required.', 'danger')
        return redirect(url_for('class.manage_students', id=id))
    
    student = User.query.get_or_404(student_id)
    if student.is_teacher:
        flash('Cannot add a teacher as a student.', 'danger')
        return redirect(url_for('class.manage_students', id=id))
    
    if student in class_.students:
        flash('Student is already in this class.', 'warning')
        return redirect(url_for('class.manage_students', id=id))
    
    class_.add_student(student)
    flash('Student added successfully!', 'success')
    return redirect(url_for('class.manage_students', id=id))

@class_bp.route('/classes/<int:id>/remove_student', methods=['POST'])
@login_required
def remove_student(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or current_user not in class_.teachers:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student_id = request.form.get('student_id')
    if not student_id:
        flash('Student ID is required.', 'danger')
        return redirect(url_for('class.manage_students', id=id))
    
    student = User.query.get_or_404(student_id)
    if student not in class_.students:
        flash('Student is not in this class.', 'warning')
        return redirect(url_for('class.manage_students', id=id))
    
    class_.remove_student(student)
    flash('Student removed successfully!', 'success')
    return redirect(url_for('class.manage_students', id=id))

@class_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_class():
    if current_user.is_teacher:
        flash('Teachers cannot join classes as students.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        code = request.form.get('class_code')
        if not code:
            flash('Class code is required.', 'danger')
            return render_template('classes/join.html')
        
        class_ = Class.query.filter_by(class_code=code).first()
        if not class_:
            flash('Invalid class code.', 'danger')
            return render_template('classes/join.html')
        
        if current_user in class_.students:
            flash('You are already in this class.', 'warning')
            return redirect(url_for('class.view_class', id=class_.id))
        
        class_.add_student(current_user)
        flash('Successfully joined the class!', 'success')
        return redirect(url_for('class.view_class', id=class_.id))
    
    return render_template('classes/join.html')
