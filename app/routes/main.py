from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.db import get_db
from datetime import date

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    print(f"DEBUG: User is authenticated: {current_user.is_authenticated}")
    return render_template("index.html")


@main_bp.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        Username = request.form.get("Username")
        Age = request.form.get("Age")
        Email = request.form.get("Email")
        Password = request.form.get("Password")
        Role = request.form.get("Role")
        db = get_db()
        # 1. Vérifier si l'utilisateur existe déjà
        user_exists = db.execute(
            "SELECT id FROM Users WHERE Username = ?", (Username,)
        ).fetchone()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.")
            return redirect(url_for("main.register"))
        # 2. Insérer le nouvel utilisateur
        db.execute(
            "INSERT INTO users (Username, Age, Email, Password, role) VALUES (?, ?, ?, ?, ?)",
            (Username, Age, Email, Password, Role),
        )
        db.commit()
        flash("Compte créé ! Vous pouvez vous connecter.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@main_bp.route("/publish", methods=["GET", "POST"])
@login_required #Seulement les users ayant un compte et connecté peuvent poster!
def publish():
    if request.method == "POST":
        titre = request.form.get("Titre")
        description = request.form.get("Description")
        localisation = request.form.get("Localisation")
        latitude = request.form.get("Latitude")
        longitude = request.form.get("Longitude")
        photo = request.files.get("Photo")
        photo_data = photo.read() if photo else None

        db = get_db()
        db.execute(
            """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Photos)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (titre, description, None, date.today(), localisation, latitude, longitude, photo_data)
        )
        db.commit()
        flash("Post publié.")
        return redirect(url_for("main.index"))
    
    return render_template("publish.html")