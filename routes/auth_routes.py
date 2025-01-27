from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from forms import LoginForm, RegistrationForm
from models.user import User
from app import db, logger

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.welcome'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                # Get the next page from the URL parameters, defaulting to welcome
                next_page = request.args.get('next', url_for('main.welcome'))
                return redirect(next_page)
            flash('Invalid username or password', 'danger')
        return render_template('auth/login.html', form=form)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        flash('An error occurred during login. Please try again.', 'danger')
        return redirect(url_for('main.home'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.welcome'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            # Check if username or email already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'danger')
                return render_template('auth/register.html', form=form)
                
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered. Please use a different email.', 'danger')
                return render_template('auth/register.html', form=form)
                
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        return render_template('auth/register.html', form=form)
    except Exception as e:
        logger.error(f"Error in register route: {str(e)}")
        flash('An error occurred during registration. Please try again.', 'danger')
        return redirect(url_for('main.home'))

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('You have been logged out successfully.', 'success')
        return redirect(url_for('main.home'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        flash('An error occurred during logout.', 'danger')
        return redirect(url_for('main.home'))
