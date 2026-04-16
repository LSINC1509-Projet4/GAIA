import os
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.db import get_db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    db = get_db()
    posts = db.execute(
        "SELECT Id, Titre, Description, Commentaire, strftime('%Y-%m-%d', Date) as Date, Localisation, Latitude, Longitude, Badges, Username, Photo FROM Posts ORDER BY Date DESC"
    ).fetchall()
    comments = db.execute(
        "SELECT * FROM Comments ORDER BY Date ASC"
    ).fetchall()
    return render_template("index.html", posts=posts, comments=comments)


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
@login_required  # Seulement les users ayant un compte et connecté peuvent poster!
def publish():
    if request.method == "POST":
        titre = request.form.get("Titre")
        description = request.form.get("Description")
        date_post = datetime.now().strftime("%Y-%m-%d")
        localisation = request.form.get("Localisation")
        latitude = request.form.get("Latitude")
        longitude = request.form.get("Longitude")
        file = request.files.get("Photo")
        filename = None
        if file and isinstance(file.filename, str) and file.filename != "":
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, "static/uploads")
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        db = get_db()
        db.execute(
            "INSERT INTO Posts (titre, description,date ,  localisation, latitude, longitude, Photo, Username) VALUES (?, ?, ?, ?, ?, ?,?,?)",
            (
                titre,
                description,
                date_post,
                localisation,
                latitude,
                longitude,
                filename,
                current_user.Username,
            ),
        )
        db.commit()
        flash("Post publié.")
        return redirect(url_for("main.index"))

    return render_template("publish.html")

@main_bp.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    contenu = request.form.get("Contenu")
    parent_id = request.form.get("Parent_Id") or None

    db = get_db()
    db.execute(
        "INSERT INTO Comments (Contenu, Date, Username, Post_Id, Parent_Id) VALUES (?, ?, ?, ?, ?)",
        (contenu, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_user.Username, post_id, parent_id)
    )
    db.commit()
    return redirect(url_for("main.index"))