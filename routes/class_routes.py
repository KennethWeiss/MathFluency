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
    try:
        from flask_wtf.csrf import validate_csrf
        validate_csrf(request.form.get('csrf_token'))
        
        class_ = Class.query.get_or_404(id)
        if not current_user.is_teacher or current_user not in class_.teachers:
            flash('Access denied.', 'danger')
            return redirect(url_for('class.manage_students', id=id))
        
        student_id = request.form.get('student_id')
        if not student_id:
            flash('Student ID is required.', 'danger')
            return redirect(url_for('class.manage_students', id=id))
        
        student = User.query.get_or_404(student_id)
        if student not in class_.students:
            flash('Student is not in this class.', 'warning')
            return redirect(url_for('class.manage_students', id=id))
        
        class_.remove_student(student)
        db.session.commit()
        flash('Student removed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while removing the student.', 'danger')
        current_app.logger.error(f"Error removing student: {str(e)}")
    
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
    class_id = request.form.get('class_id')
    if not class_id:
        flash('Please select a class', 'error')
        return redirect(url_for('class.list_classes'))
    
    class_ = Class.query.get_or_404(class_id)
    
    # Verify the current user is a teacher of this class
    if current_user not in class_.teachers:
        flash('You do not have permission to add students to this class', 'error')
        return redirect(url_for('class.list_classes'))
    
    try:
        from flask import current_app
        current_app.logger.info(f"Starting student upload for class {class_id}")
        
        # Read and parse CSV
        rows = read_and_parse_csv('test_students.csv')
        current_app.logger.info(f"Read {len(rows)} rows from CSV")
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for row in rows:
            try:
                # Skip empty rows
                if not any(row):
                    continue
                    
                # Get student data
                first_name = row['first_name'].strip()
                last_name = row['last_name'].strip()
                email = row.get('email', '').strip().lower() or f"{first_name.lower()}.{last_name.lower()}@mathfluency.com"
                password = row.get('password', '').strip() or ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Validate data
                if not first_name or not last_name:
                    error_count += 1
                    error_messages.append(f"Missing name fields in row: {row}")
                    continue
                    
                if '@' not in email or '.' not in email.split('@')[1]:
                    error_count += 1
                    error_messages.append(f"Invalid email format: {email}")
                    continue
                
                # Check if user exists or create new
                user = User.query.filter_by(email=email).first()
                if not user:
                    user = create_new_user(first_name, last_name, email, password)
                    db.session.add(user)
                    
                    # Send welcome email
                    try:
                        from services.email_service import send_welcome_email
                        send_welcome_email(
                            email=email,
                            password=password,
                            first_name=first_name,
                            class_name=class_.name
                        )
                        current_app.logger.info(f"Sent welcome email to {email}")
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Failed to send welcome email to {email}: {str(e)}")
                        current_app.logger.error(f"Email send error: {str(e)}")
                
                # Add user to class if not already enrolled
                if user not in class_.students:
                    class_.students.append(user)
                    success_count += 1
                    current_app.logger.info(f"Added user {email} to class {class_id}")
                else:
                    error_count += 1
                    error_messages.append(f"Student {email} already in class")
                    current_app.logger.info(f"User {email} already in class")
            
            except Exception as e:
                error_count += 1
                error_messages.append(f"Error processing row: {row} - {str(e)}")
                current_app.logger.error(f"Error processing row: {str(e)}")
        
        db.session.commit()
        current_app.logger.info(f"Commit successful. Added {success_count} students, {error_count} errors")
        
        # Flash summary message
        if success_count > 0:
            flash(f'Successfully added {success_count} student(s) to the class', 'success')
        if error_count > 0:
            flash(f'Failed to add {error_count} student(s). Check the error log for details', 'warning')
            for msg in error_messages:
                flash(str(msg), 'error')
                current_app.logger.error(f"Error: {str(msg)}")
                
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV file: {str(e)}', 'error')
        current_app.logger.error(f"Error processing CSV: {str(e)}")
    
    return redirect(url_for('class.list_classes'))

@class_bp.route('/student/<int:student_id>/clear_progress', methods=['POST'])
@login_required
def clear_student_progress(student_id):
    if not current_user.is_teacher:
        flash('Only teachers can clear student progress.', 'danger')
        return redirect(url_for('main.home'))
    
    # Get the student
    student = User.query.get_or_404(student_id)
    
    # Verify the student is in one of the teacher's classes
    student_in_class = False
    for class_ in current_user.teaching_classes:
        if student in class_.students:
            student_in_class = True
            break
    
    if not student_in_class:
        flash('You can only clear progress for students in your classes.', 'danger')
        return redirect(url_for('class.list_classes'))
    
    try:
        # Delete practice attempts
        PracticeAttempt.query.filter_by(user_id=student_id).delete()
        
        # Delete assignment progress
        AssignmentProgress.query.filter_by(student_id=student_id).delete()
        
        # Delete attempt history
        AttemptHistory.query.filter_by(student_id=student_id).delete()
        
        # Commit the changes
        db.session.commit()
        
        flash(f'Successfully cleared progress data for {student.username}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while clearing progress data.', 'danger')
        logger.error(f"Error clearing progress for student {student_id}: {str(e)}")
    
    # Redirect back to the class view
    return redirect(request.referrer or url_for('class.list_classes'))

def read_and_parse_csv(file_path):
    """Read and parse CSV file into list of dictionaries"""
    from flask import current_app
    
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
        current_app.logger.info(f"File content:\n{file_content}")
        
    # Handle BOM character if present
    if file_content.startswith('\ufeff'):
        file_content = file_content[1:]
        current_app.logger.info("Removed BOM character from file content")

    # Get headers and normalize
    lines = file_content.splitlines()
    headers = [h.strip().lower() for h in lines[0].split(',')]
    
    # Create list of rows as dictionaries
    rows = []
    for line in lines[1:]:
        if line.strip():
            values = [v.strip() for v in line.split(',')]
            rows.append(dict(zip(headers, values)))
    
    return rows

def create_new_user(first_name, last_name, email, password):
    """Create new user with generated username"""
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        is_teacher=False
    )
    user.set_password(password)
    return user
