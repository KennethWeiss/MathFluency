from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.class_ import Class
from models.user import User
from app import db
import io
import csv
import random
import string

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
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    elif not current_user.is_teacher and current_user not in class_.students:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
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

@class_bp.route('/upload_students', methods=['POST'])
@login_required
def upload_students():
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('class.list_classes'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('class.list_classes'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file', 'error')
        return redirect(url_for('class.list_classes'))
    
    class_id = request.form.get('class_id')
    if not class_id:
        flash('Please select a class', 'error')
        return redirect(url_for('class.list_classes'))
    
    class_ = Class.query.get_or_404(class_id)
    
    # Verify the teacher owns this class
    if class_.teacher_id != current_user.id:
        flash('You do not have permission to add students to this class', 'error')
        return redirect(url_for('class.list_classes'))
    
    try:
        # Read and decode the CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for row in csv_reader:
            try:
                if len(row) != 3:
                    error_count += 1
                    error_messages.append(f"Invalid row format: {','.join(row)}")
                    continue
                
                first_name, last_name, email = row
                
                # Check if user already exists
                user = User.query.filter_by(email=email).first()
                if not user:
                    # Create new user with random password
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                    user = User(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        username=email.split('@')[0],
                        role='student'
                    )
                    user.set_password(password)
                    db.session.add(user)
                    
                    # TODO: Send email with login credentials
                    # send_welcome_email(email, password)
                
                # Add user to class if not already enrolled
                if user not in class_.students:
                    class_.students.append(user)
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"Student {email} already in class")
            
            except Exception as e:
                error_count += 1
                error_messages.append(f"Error processing row: {','.join(row)} - {str(e)}")
        
        db.session.commit()
        
        # Flash summary message
        if success_count > 0:
            flash(f'Successfully added {success_count} student(s) to the class', 'success')
        if error_count > 0:
            flash(f'Failed to add {error_count} student(s). Check the error log for details', 'warning')
            for msg in error_messages:
                flash(msg, 'error')
                
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV file: {str(e)}', 'error')
    
    return redirect(url_for('class.list_classes'))
