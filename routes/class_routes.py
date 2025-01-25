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
        # Read from test_students.csv
        with open('test_students.csv', 'r', encoding='utf-8') as f:
            file_content = f.read()
            current_app.logger.info(f"File content:\n{file_content}")
        # Handle BOM character if present
        if file_content.startswith('\ufeff'):
            file_content = file_content[1:]
            current_app.logger.info("Removed BOM character from file content")

        # Get first line and normalize headers
        first_line = file_content.split('\n')[0].strip()
        actual_headers = [h.strip().lower() for h in first_line.split(',')]
        # Create mapping from actual headers to required names
        header_map = {}
        for idx, header in enumerate(actual_headers):
            header_lower = header.strip().lower()
            if 'first' in header_lower and 'name' in header_lower:
                header_map['first_name'] = idx
            elif 'last' in header_lower and 'name' in header_lower:
                header_map['last_name'] = idx
            elif 'email' in header_lower:
                header_map['email'] = idx
            elif 'password' in header_lower:
                header_map['password'] = idx
        
        # Generate email and password if not in CSV
        if 'Email' not in header_map:
            header_map['email'] = 'generated'
        if 'Password' not in header_map:
            header_map['password'] = 'generated'
        
        # Define minimum required columns
        required_columns = {
            'first_name': 'first_name',
            'last_name': 'last_name',
        }
        
        # Check for required columns
        missing_columns = []
        for col_name, display_name in required_columns.items():
            if col_name not in actual_headers:
                print(f"Missing column: {display_name}")
                missing_columns.append(display_name)
        
        if missing_columns:
            flash(
                f'CSV is missing required columns: {", ".join(missing_columns)}. '
                f'Found columns: {first_line}. '
                f'Required columns: First Name, Last Name',
                'error'
            )
            return redirect(url_for('class.list_classes'))
        
        # Create mapping from actual headers to required names
        header_map = {}
        for idx, header in enumerate(actual_headers):
            if header in required_columns:
                header_map[required_columns[header]] = idx
            
        # Split file content into lines and parse each row
        rows = []
        for line in file_content.splitlines():
            if line.strip():  # Skip empty lines
                rows.append([field.strip() for field in line.split(',')])
        current_app.logger.info(f"Read {len(rows)} rows from CSV")
        print("Rows:")
        print(rows)
        print("Rows[0]:")
        print(rows[0])   
        # Create list of emails for duplicate checking
        emails = []
        for row in rows[1:]:  # Skip header row
            if 'email' in header_map:
                email_index = header_map['email']
                print("Email index:", email_index)
                if len(row) > email_index:
                    email = row[email_index].strip().lower()
                    emails.append(email)
            else:
                # Generate email if not in CSV
                first_name = row[header_map['first_name']].strip()
                last_name = row[header_map['last_name']].strip()
                email = f"{first_name.lower()}.{last_name.lower()}@mathfluency.com"
                emails.append(email)
        current_app.logger.info(f"Extracted {len(emails)} emails from CSV")
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for row in rows:
            try:
                # Skip empty rows
                if not any(row):
                    continue
                    
                # Get values using header mapping
                first_name = row[header_map['first_name']].strip()
                last_name = row[header_map['last_name']].strip()
                
                # Generate email if not in CSV
                if header_map['email'] == 'generated':
                    email = f"{first_name.lower()}.{last_name.lower()}@mathfluency.com"
                else:
                    email = row[header_map['email']].strip().lower()
                
                # Generate password if not in CSV
                if header_map['password'] == 'generated':
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                else:
                    password = row[header_map['password']].strip()
                
                # Validate email format
                if '@' not in email or '.' not in email.split('@')[1]:
                    error_count += 1
                    error_messages.append(f"Invalid email format: {email}")
                    continue
                
                # Check for duplicate email in current CSV
                if emails.count(email) > 1:
                    error_count += 1
                    error_messages.append(f"Duplicate email in CSV: {email}")
                    continue
                    
                current_app.logger.info(f"Processing row {rows.index(row)+1}: {first_name} {last_name} <{email}>")
                current_app.logger.debug(f"Full row data: {row}")
                
                # Check if user already exists
                user = User.query.filter_by(email=email).first()
                current_app.logger.info(f"User lookup result: {'Found' if user else 'Not found'}")
                if user:
                    current_app.logger.debug(f"Existing user details: {user.id} {user.email}")
                if not user:
                    # Validate password
                    if len(password) < 4:
                        error_count += 1
                        error_messages.append(f"Password must be at least 4 characters for {email}")
                        continue
                        
                    # Generate unique username
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
                    db.session.add(user)
                    
                    # Send welcome email with login credentials
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
                    current_app.logger.info(f"Adding user {email} to class {class_id}")
                    class_.students.append(user)
                    success_count += 1
                else:
                    error_count += 1
                    error_messages.append(f"Student {email} already in class")
                    current_app.logger.info(f"User {email} already in class")
            
            except Exception as e:
                error_count += 1
                error_messages.append(f"Error processing row: {','.join(row)} - {str(e)}")
        
        db.session.commit()
        current_app.logger.info(f"Commit successful. Added {success_count} students, {error_count} errors")
        
        # Flash summary message
        if success_count > 0:
            flash(f'Successfully added {success_count} student(s) to the class', 'success')
        if error_count > 0:
            flash(f'Failed to add {error_count} student(s). Check the error log for details', 'warning')
            for msg in error_messages:
                if isinstance(msg, list):
                    flash(', '.join(msg), 'error')
                    current_app.logger.error(f"Error: {', '.join(msg)}")
                else:
                    flash(str(msg), 'error')
                    current_app.logger.error(f"Error: {str(msg)}")
                
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing CSV file: {str(e)}', 'error')
    
    return redirect(url_for('class.list_classes'))
