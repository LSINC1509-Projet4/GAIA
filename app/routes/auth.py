# Code d'authification à la base données (de connexion au site ) pour un utilisateurs
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.db import get_db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        Username = request.form.get("Username")
        Password = request.form.get("Password")

        db = get_db()
        user_row = db.execute(
            "SELECT * FROM Users WHERE Username = ?", (Username,)
        ).fetchone()

        if user_row and user_row["Password"] == Password:
            user = User(
                user_row["Id"],
                user_row["Username"],
                user_row["Email"],
                user_row["Role"],
            )
            login_user(user)
            return redirect(url_for("main.index"))

        flash("Nom d'utilisateur ou mot de passe incorrect.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
