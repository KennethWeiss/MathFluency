from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from models.user import User
from models.class_ import Class
from models.assignment import Assignment

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    classes = Class.query.all()
    assignments = Assignment.query.all()
    return render_template('admin/dashboard.html', 
                        users=users,
                        classes=classes,
                        assignments=assignments)

@admin_bp.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'Made {user.email} an admin.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/toggle_teacher/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_teacher(user_id):
    user = User.query.get_or_404(user_id)
    user.is_teacher = not user.is_teacher
    db.session.commit()
    status = "teacher" if user.is_teacher else "non-teacher"
    flash(f'Updated {user.email} to {status}.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    # Don't allow admin to remove their own admin status
    if user_id == current_user.id:
        flash('You cannot remove your own admin status.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = "admin" if user.is_admin else "non-admin"
    flash(f'Updated {user.email} to {status}.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash('Cannot delete your own account!', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Deleted user {user.email}.', 'success')
    return redirect(url_for('admin.admin_dashboard'))
