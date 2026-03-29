from flask import Blueprint
from app.db import get_db
from flask_login import login_required
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return "Bienvenue"