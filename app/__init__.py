from flask import Flask 
import os 

def create_app():
    app = Flask(__name__)
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app