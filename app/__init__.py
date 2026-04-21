import os

from flask import Flask
from flask_login import LoginManager

from .db import close_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "Gaia")

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.db import get_db
        from app.models import User

        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE Id = ?", (user_id,)).fetchone()
        if user:
            return User(user["Id"], user["Username"], user["Email"], user["Role"])
        return None

    app.teardown_appcontext(close_db)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        from app.db import init_db

        init_db()
    return app
