from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models.class_ import Class
from models.user import User
from datetime import datetime

class_bp = Blueprint('class', __name__)

@class_bp.route('/classes')
@login_required
def list_classes():
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.index'))
    
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('classes/list.html', classes=classes)

@class_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
def create_class():
    if not current_user.is_teacher:
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Class name is required.', 'danger')
            return render_template('classes/create.html')
        
        new_class = Class(
            name=name,
            description=description,
            teacher_id=current_user.id
        )
        
        db.session.add(new_class)
        db.session.commit()
        
        flash('Class created successfully!', 'success')
        return redirect(url_for('class.view_class', id=new_class.id))
    
    return render_template('classes/create.html')

@class_bp.route('/classes/<int:id>')
@login_required
def view_class(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or class_.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student_count = class_.students.count()

    assignment_count = class_.assignments.count()

    return render_template('classes/view.html', class_=class_, student_count=student_count, assignment_count=assignment_count)

@class_bp.route('/classes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_class(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or class_.teacher_id != current_user.id:
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
    if not current_user.is_teacher or class_.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all students not in this class
    available_students = User.query.filter_by(is_teacher=False).all()
    return render_template('classes/manage_students.html', 
                        class_=class_,
                        available_students=available_students)

@class_bp.route('/classes/<int:id>/add_student', methods=['POST'])
@login_required
def add_student(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or class_.teacher_id != current_user.id:
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
    
    class_.students.append(student)
    db.session.commit()
    
    flash('Student added successfully!', 'success')
    return redirect(url_for('class.manage_students', id=id))

@class_bp.route('/classes/<int:id>/remove_student', methods=['POST'])
@login_required
def remove_student(id):
    class_ = Class.query.get_or_404(id)
    if not current_user.is_teacher or class_.teacher_id != current_user.id:
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
    
    class_.students.remove(student)
    db.session.commit()
    
    flash('Student removed successfully!', 'success')
    return redirect(url_for('class.manage_students', id=id))
