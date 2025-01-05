from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user, current_user
from models.class_ import Class
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.welcome'))
    return render_template('index.html')

@main_bp.route('/welcome')
@login_required
def welcome():
    if current_user.is_teacher:
        # Get all classes where this teacher is teaching
        classes = Class.query.join(Class.teachers).filter(Class.teachers.contains(current_user)).all()
        
        # Get all students from these classes
        students = set()
        for class_ in classes:
            # Force load of students
            class_.students.all()
            students.update(class_.students)
        
        return render_template('welcome.html', 
                            is_teacher=True,
                            students=list(students),
                            classes=classes)
    else:
        # Get all classes where this student is enrolled
        enrolled_classes = Class.query.join(Class.students).filter(Class.students.contains(current_user)).all()
        
        # Force load of teachers for each class
        for class_ in enrolled_classes:
            class_.teachers.all()
            
        return render_template('welcome.html',
                            is_teacher=False,
                            enrolled_classes=enrolled_classes)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
