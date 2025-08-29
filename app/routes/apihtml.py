from flask import Blueprint, render_template


apihtml_bp = Blueprint('apihtml', __name__)

@apihtml_bp.route('/apihtml')


def apihtml():
    return render_template('apihtml.html')
