from flask import Blueprint
from app.db import get_db
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return "Bienvenue"