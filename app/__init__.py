from flask import Flask 
from .db import close_db
import os 

def create_app():
    app = Flask(__name__)

    # indique de fermer l'accès à la fin de chaque page
    app.teardown_appcontext(close_db)

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app