import os
from datetime import datetime

import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
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
    search = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    query = """SELECT Id, Titre, Description, Commentaire,
               strftime('%Y-%m-%d', Date) as Date,
               Localisation, Latitude, Longitude, Badges, Username, Photo
               FROM Posts WHERE 1=1"""
    params = []

    if search:
        query += " AND (Titre LIKE ? OR Description LIKE ? OR Localisation LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if location:
        query += " AND Localisation = ?"
        params.append(location)

    query += " ORDER BY Date DESC"

    posts = db.execute(query, params).fetchall()
    comments = db.execute("SELECT * FROM Comments ORDER BY Date ASC").fetchall()
    locations_list = db.execute("SELECT DISTINCT Localisation FROM Posts ORDER BY Localisation").fetchall()
    return render_template(
        "index.html",
        posts=posts,
        comments=comments,
        search=search,
        location=location,
        locations_list=locations_list,
    )


@main_bp.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        Username = request.form.get("Username")
        Age = request.form.get("Age")
        Email = request.form.get("Email")
        Password = request.form.get("Password")
        Role = request.form.get("Role")
        db = get_db()
        user_exists = db.execute(
            "SELECT id FROM Users WHERE Username = ?", (Username,)
        ).fetchone()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.")
            return redirect(url_for("main.register"))
        db.execute(
            "INSERT INTO users (Username, Age, Email, Password, role) VALUES (?, ?, ?, ?, ?)",
            (Username, Age, Email, Password, Role),
        )
        db.commit()
        flash("Compte créé ! Vous pouvez vous connecter.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@main_bp.route("/publish", methods=["GET", "POST"])
@login_required
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
            "INSERT INTO Posts (titre, description, date, localisation, latitude, longitude, Photo, Username) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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

@main_bp.route("/profile")
@login_required
def profile():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM Posts WHERE Username = ? ORDER BY Date DESC", (current_user.Username,)
    ).fetchall()
    comments = db.execute(
        "SELECT * FROM Comments WHERE Username = ? ORDER BY Date DESC", (current_user.Username,)
    ).fetchall()
    profile_user = {"Username": current_user.Username, "Role": current_user.Role}
    return render_template("profile.html", posts=posts, comments=comments, profile_user=profile_user)

@main_bp.route("/profile/<username>")
@login_required
def user_profile(username):
    """
    Input : username
    -> Recupere le role, les comm, les posts de l'utilisateurs et on fill la page profile avec
    """
    db = get_db()
    role = db.execute("SELECT Role FROM Users WHERE Username = ?", (username,)).fetchone()["Role"]
    posts = db.execute(
        "SELECT * FROM Posts WHERE Username = ? ORDER BY Date DESC", (username,)
    ).fetchall()
    comments = db.execute(
        "SELECT * FROM Comments WHERE Username = ? ORDER BY Date DESC", (username,)
    ).fetchall()
    profile_user = {"Username": username, "Role": role}
    return render_template("profile.html", posts=posts, comments=comments, profile_user=profile_user)

@main_bp.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    contenu = request.form.get("Contenu")
    parent_id = request.form.get("Parent_Id") or None

    db = get_db()
    db.execute(
        "INSERT INTO Comments (Contenu, Date, Username, Post_Id, Parent_Id) VALUES (?, ?, ?, ?, ?)",
        (
            contenu,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_user.Username,
            post_id,
            parent_id,
        ),
    )
    db.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/api/animals")
@login_required
def get_animals():
    query = request.args.get("q", "")
    if len(query) < 2:
        return jsonify([])

    url = f"https://api.inaturalist.org/v1/taxa/autocomplete?q={query}&locale=fr"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append(
                {
                    "name": item.get("preferred_common_name") or item.get("name"),
                    "scientific": item.get("name"),
                }
            )
        return jsonify(results)
    except Exception as e:
        print(f"Error fetching from iNaturalist: {e}")
        return jsonify([])


@main_bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    db = get_db()
    post = db.execute(
        "SELECT Id, Titre, Description, Localisation, Latitude, Longitude, Photo, Username FROM Posts WHERE Id = ?",
        (post_id,),
    ).fetchone()

    if post is None:
        flash("Post introuvable.")
        return redirect(url_for("main.index"))

    if current_user.Username != post["Username"] and current_user.Role != "Admin":
        flash("Action non autorisée.")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        titre = request.form.get("Titre")
        description = request.form.get("Description")
        localisation = request.form.get("Localisation")
        latitude = request.form.get("Latitude")
        longitude = request.form.get("Longitude")
        file = request.files.get("Photo")
        filename = post["Photo"]
        if file and isinstance(file.filename, str) and file.filename != "":
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.root_path, "static/uploads")
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            file.save(os.path.join(upload_path, filename))

        db.execute(
            "UPDATE Posts SET Titre=?, Description=?, Localisation=?, Latitude=?, Longitude=?, Photo=? WHERE Id=?",
            (titre, description, localisation, latitude, longitude, filename, post_id),
        )
        db.commit()
        flash("Post modifié.")
        return redirect(url_for("main.index"))

    return render_template("publish.html", post=post)


@main_bp.route("/carte")
@login_required
def carte():
    db = get_db()
    posts = db.execute(
        "SELECT Id, Titre, Description, strftime('%Y-%m-%d', Date) as Date, "
        "Localisation, Latitude, Longitude, Username, Photo "
        "FROM Posts WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL"
    ).fetchall()
    return render_template("map.html", posts=[dict(row) for row in posts])


@main_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    post = db.execute(
        "SELECT Id, Username FROM Posts WHERE Id = ?", (post_id,)
    ).fetchone()

    if post is None:
        flash("Post introuvable.")
        return redirect(url_for("main.index"))

    if current_user.Username != post["Username"] and current_user.Role != "Admin":
        flash("Action non autorisée.")
        return redirect(url_for("main.index"))

    db.execute("DELETE FROM Comments WHERE Post_Id = ?", (post_id,))
    db.execute("DELETE FROM Posts WHERE Id = ?", (post_id,))
    db.commit()
    flash("Post supprimé.")
    return redirect(url_for("main.index"))
