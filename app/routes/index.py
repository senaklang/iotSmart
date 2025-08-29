from flask import Blueprint, render_template

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
@index_bp.route('/index')
def dashboard():
    return render_template('index.html')
