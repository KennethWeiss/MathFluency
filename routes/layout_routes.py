from flask import Blueprint, render_template
from flask_login import login_required

layout_bp = Blueprint('layout', __name__, url_prefix='/layout')

@layout_bp.route('/deltamath')
@login_required
def deltamath_layout():
    return render_template('layouts/deltamath_style.html')

@layout_bp.route('/99math')
@login_required
def ninetynine_math_layout():
    return render_template('layouts/99math_style.html')

@layout_bp.route('/learning-path')
@login_required
def learning_path_layout():
    return render_template('layouts/learning_path.html')

@layout_bp.route('/dashboard')
@login_required
def dashboard_layout():
    return render_template('layouts/dashboard_style.html')

@layout_bp.route('/mastery-grid')
@login_required
def mastery_grid_layout():
    return render_template('layouts/mastery_grid.html')

@layout_bp.route('/skill-tree')
@login_required
def skill_tree_layout():
    return render_template('layouts/skill_tree.html')

@layout_bp.route('/timeline')
@login_required
def timeline_layout():
    return render_template('layouts/timeline.html')

@layout_bp.route('/challenge')
@login_required
def challenge_layout():
    return render_template('layouts/challenge_mode.html')

@layout_bp.route('/quest')
@login_required
def quest_layout():
    return render_template('layouts/quest_style.html')
