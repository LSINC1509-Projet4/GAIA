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
from app.xp_logic import calculate_tot,calcul_levels
from app.xp_logic import badge
main_bp = Blueprint("main", __name__)

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
        user_exists = db.execute("SELECT id FROM Users WHERE Username = ?", (Username,)).fetchone()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.")
            return redirect(url_for("main.register"))

        # 2. Insérer le nouvel utilisateur d'abord
        cursor = db.execute(
            "INSERT INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
            (Username, Age, Email, Password, Role),
        )

        # 3. RÉCUPÉRER L'ID GÉNÉRÉ
        new_user_id = cursor.lastrowid

        # 4. CRÉER LES STATS POUR CET ID
        db.execute("INSERT INTO UserStats (UserId, NbrePostsAlltime, NBreLikesAlltime, TotalXP, CurrentLevel) VALUES (?, 0, 0, 0, 1)", (new_user_id,))

        db.commit()
        flash("Compte créé ! Connectez-vous.")
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
        db.execute("UPDATE UserStats SET NbrePostsAlltime = NbrePostsAlltime + 1 WHERE UserId = ?", (current_user.id,))
        stats = db.execute("SELECT NbrePostsAlltime, NBreLikesAlltime FROM UserStats WHERE UserId = ?", (current_user.id,)).fetchone()
        if stats:
            new_xp = calculate_tot(stats["NbrePostsAlltime"], stats["NBreLikesAlltime"])
            new_level = calcul_levels(new_xp)
            db.execute("UPDATE UserStats SET TotalXP = ?, CurrentLevel = ? WHERE UserId = ?", (new_xp, new_level, current_user.id))

        db.commit()
        flash("Post publié.")
        return redirect(url_for("main.index"))

    return render_template("publish.html")

@main_bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    db = get_db()
    existing_like = db.execute("SELECT * FROM Likes WHERE UserId = ? AND PostId = ?", (current_user.id, post_id)).fetchone()

    post = db.execute("SELECT Username FROM Posts WHERE Id = ?", (post_id,)).fetchone()
    if not post:
        return redirect(url_for('main.index'))

    author = db.execute("SELECT Id FROM Users WHERE Username = ?", (post["Username"],)).fetchone()
    author_id = author["Id"] if author else None

    if existing_like:
        db.execute("DELETE FROM Likes WHERE UserId = ? AND PostId = ?", (current_user.id, post_id))

        if author_id:
            db.execute("UPDATE UserStats SET NBreLikesAlltime = MAX(0, NBreLikesAlltime - 1) WHERE UserId = ?", (author_id,))
        flash("Arrosage annulé.")
    else:
        db.execute("INSERT INTO Likes (UserId, PostId) VALUES (?, ?)", (current_user.id, post_id))
        if author_id:
            db.execute("UPDATE UserStats SET NBreLikesAlltime = NBreLikesAlltime + 1 WHERE UserId = ?", (author_id,))
        flash("Post arrosé !")

    if author_id:
        stats = db.execute("SELECT NbrePostsAlltime, NBreLikesAlltime FROM UserStats WHERE UserId = ?", (author_id,)).fetchone()
        if stats:
            new_xp = calculate_tot(stats["NbrePostsAlltime"], stats["NBreLikesAlltime"])
            new_level = calcul_levels(new_xp)
            db.execute("UPDATE UserStats SET TotalXP = ?, CurrentLevel = ? WHERE UserId = ?", (new_xp, new_level, author_id))

    db.commit()
    return redirect(url_for('main.index'))


@main_bp.route("/")
@login_required
def index():
    db = get_db()
    posts = db.execute(
        """SELECT Posts.Id, Titre, Description, Commentaire, strftime('%Y-%m-%d', Date) as Date,
                  Localisation, Latitude, Longitude, Posts.Username, Photo,
                  (SELECT COUNT(*) FROM Likes WHERE PostId = Posts.Id) as LikeCount,
                  UserStats.CurrentLevel
           FROM Posts
           LEFT JOIN Users ON Posts.Username = Users.Username
           LEFT JOIN UserStats ON Users.Id = UserStats.UserId
           ORDER BY Date DESC"""
    ).fetchall()
    return render_template("index.html", posts=posts, get_badge=badge)
