from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user, current_user

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
        # Get all students for this teacher
        students = current_user.students
        classes = current_user.classes
        return render_template('welcome.html', 
                            is_teacher=True,
                            students=students,
                            classes=classes)
    else:
        # Get the student's enrolled class
        enrolled_class = current_user.enrolled_class
        return render_template('welcome.html',
                            is_teacher=False,
                            enrolled_class=enrolled_class)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
