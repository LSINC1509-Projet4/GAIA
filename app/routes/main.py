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
from app.xp_logic import badge, calcul_levels, calculate_tot

main_bp = Blueprint("main", __name__)


def log_action(db, user_id, action_type, target_id=None, target_type=None, detail=None):
    # ajoute une action dans UserLogs
    db.execute(
        "INSERT INTO UserLogs (User_Id, Action_Type, Target_Id, Target_Type, Detail) VALUES (?, ?, ?, ?, ?)",
        (user_id, action_type, target_id, target_type, detail),
    )


@main_bp.route("/")
@login_required
def index():
    db = get_db()
    search = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    animal = request.args.get("animal", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    sort = request.args.get("sort", "recent")

    # Jointure ajoutée pour lier Posts avec Especes (pour le Titre) et Users (pour le Username)
    query = """SELECT Posts.Id, Especes.Nom as Titre, Description, Commentaire,
               strftime('%Y-%m-%d', Date) as Date,
               Localisation, Latitude, Longitude, Badges, Users.Username as Username, Photo,
               (SELECT COUNT(*) FROM Likes WHERE PostId = Posts.Id) as LikeCount,
               UserStats.CurrentLevel
               FROM Posts
               LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
               LEFT JOIN Users ON Posts.User_Id = Users.Id
               LEFT JOIN UserStats ON Users.Id = UserStats.UserId
               WHERE 1=1"""
    params = []

    if search:
        query += " AND (Especes.Nom LIKE ? OR Description LIKE ? OR Localisation LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if location:
        query += " AND Localisation = ?"
        params.append(location)

    if animal:
        query += " AND Especes.Nom LIKE ?"
        params.append(f"%{animal}%")

    if date_from:
        query += " AND Date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND Date <= ?"
        params.append(date_to)

    if current_user.Role != "Admin":
        query += " AND (SELECT COUNT(*) FROM Report WHERE post_id = Posts.Id) < 3"

    query += " AND Posts.Id NOT IN (SELECT post_id FROM Report WHERE reporter_id = ? AND post_id IS NOT NULL)"
    params.append(current_user.id)

    if sort == "old":
        query += " ORDER BY Date ASC"
    elif sort == "az":
        query += " ORDER BY Especes.Nom ASC"
    elif sort == "za":
        query += " ORDER BY Especes.Nom DESC"
    else:
        query += " ORDER BY Date DESC"

    posts = db.execute(query, params).fetchall()

    # Récupération du pseudo dans la table des commentaires
    comments = db.execute("""
        SELECT Comments.*, Users.Username as Username
        FROM Comments
        JOIN Users ON Comments.User_Id = Users.Id
        ORDER BY Date ASC
    """).fetchall()

    locations_list = db.execute(
        "SELECT DISTINCT Localisation FROM Posts ORDER BY Localisation"
    ).fetchall()

    # La liste d'animaux se base désormais sur la table Especes
    animals_list = db.execute(
        "SELECT DISTINCT Nom as Titre FROM Especes ORDER BY Nom"
    ).fetchall()

    return render_template(
        "index.html",
        posts=posts,
        comments=comments,
        search=search,
        location=location,
        animal=animal,
        date_from=date_from,
        date_to=date_to,
        locations_list=locations_list,
        animals_list=animals_list,
        sort=sort,
        get_badge=badge,
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

        cursor = db.execute(
            "INSERT INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
            (Username, Age, Email, Password, Role),
        )

        new_user_id = cursor.lastrowid

        db.execute(
            "INSERT INTO UserStats (UserId, NbrePostsAlltime, NBreLikesAlltime, TotalXP, CurrentLevel) VALUES (?, 0, 0, 0, 1)",
            (new_user_id,),
        )

        db.commit()
        flash("Compte créé ! Connectez-vous.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@main_bp.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    if request.method == "POST":
        nom_espece = request.form.get("Titre")
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

        # Gestion de l'espèce : on la cherche, ou on la crée si elle n'existe pas
        espece = db.execute("SELECT Id FROM Especes WHERE Nom = ?", (nom_espece,)).fetchone()
        if espece:
            espece_id = espece["Id"]
        else:
            cursor = db.execute("INSERT INTO Especes (Nom) VALUES (?)", (nom_espece,))
            espece_id = cursor.lastrowid

        db.execute(
            "INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, Photo, User_Id, Espece_Id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (description, date_post, localisation, latitude, longitude, filename, current_user.id, espece_id),
        )

        stats = db.execute(
            "SELECT NbrePostsAlltime, NBreLikesAlltime FROM UserStats WHERE UserId = ?",
            (current_user.id,)
        ).fetchone()

        if not stats:
            db.execute("INSERT INTO UserStats (UserId, NbrePostsAlltime, NBreLikesAlltime, TotalXP, CurrentLevel) VALUES (?, 0, 0, 0, 1)", (current_user.id,))
            nbre_posts = 0
            nbre_likes = 0
        else:
            nbre_posts = stats["NbrePostsAlltime"]
            nbre_likes = stats["NBreLikesAlltime"]

        nbre_posts += 1
        new_xp = calculate_tot(nbre_posts, nbre_likes)
        new_level = calcul_levels(new_xp)
        db.execute(
            "UPDATE UserStats SET NbrePostsAlltime = ?, TotalXP = ?, CurrentLevel = ? WHERE UserId = ?",
            (nbre_posts, new_xp, new_level, current_user.id)
        )

        post_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        log_action(db, current_user.id, "POST_CREATED", post_id, "post")
        db.commit()

        flash("Post publié avec succès ! +50 XP 🌱")
        return redirect(url_for("main.index"))
    return render_template("publish.html")


@main_bp.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    db = get_db()
    existing_like = db.execute(
        "SELECT * FROM Likes WHERE UserId = ? AND PostId = ?",
        (current_user.id, post_id),
    ).fetchone()

    post = db.execute("SELECT User_Id FROM Posts WHERE Id = ?", (post_id,)).fetchone()
    if not post:
        return redirect(url_for("main.index"))

    author_id = post["User_Id"]

    if existing_like:
        db.execute(
            "DELETE FROM Likes WHERE UserId = ? AND PostId = ?",
            (current_user.id, post_id),
        )
        if author_id:
            db.execute(
                "UPDATE UserStats SET NBreLikesAlltime = MAX(0, NBreLikesAlltime - 1) WHERE UserId = ?",
                (author_id,),
            )
        flash("Arrosage annulé.")
    else:
        db.execute(
            "INSERT INTO Likes (UserId, PostId) VALUES (?, ?)",
            (current_user.id, post_id),
        )
        if author_id:
            db.execute(
                "UPDATE UserStats SET NBreLikesAlltime = NBreLikesAlltime + 1 WHERE UserId = ?",
                (author_id,),
            )
        flash("Post arrosé !")

    if author_id:
        stats = db.execute(
            "SELECT NbrePostsAlltime, NBreLikesAlltime FROM UserStats WHERE UserId = ?",
            (author_id,),
        ).fetchone()
        if stats:
            new_xp = calculate_tot(stats["NbrePostsAlltime"], stats["NBreLikesAlltime"])
            new_level = calcul_levels(new_xp)
            db.execute(
                "UPDATE UserStats SET TotalXP = ?, CurrentLevel = ? WHERE UserId = ?",
                (new_xp, new_level, author_id),
            )

    db.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/admin/reports")
@login_required
def admin_reports():
    if current_user.Role != "Admin":
        flash("Accès réservé aux administrateurs.")
        return redirect(url_for("main.index"))

    db = get_db()
    reported = db.execute("""
        SELECT p.Id, e.Nom as Titre, u.Username as Username, p.Photo, p.Localisation,
               strftime('%Y-%m-%d', p.Date) as Date,
               COUNT(r.id) as nb_reports
        FROM Posts p
        LEFT JOIN Especes e ON p.Espece_Id = e.Id
        JOIN Report r ON r.post_id = p.Id
        JOIN Users u ON p.User_Id = u.Id
        GROUP BY p.Id
        ORDER BY nb_reports DESC
    """).fetchall()

    return render_template("admin_reports.html", reported=reported)


@main_bp.route("/admin/reports/<int:post_id>/dismiss", methods=["POST"])
@login_required
def dismiss_reports(post_id):
    if current_user.Role != "Admin":
        flash("Accès réservé aux administrateurs.")
        return redirect(url_for("main.index"))

    db = get_db()
    db.execute("DELETE FROM Report WHERE post_id = ?", (post_id,))
    db.commit()
    flash("Signalements ignorés.")
    return redirect(url_for("main.admin_reports"))


@main_bp.route("/profile")
@login_required
def profile():
    db = get_db()
    posts = db.execute("""
        SELECT Posts.*, Especes.Nom as Titre, Users.Username as Username
        FROM Posts
        LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
        JOIN Users ON Posts.User_Id = Users.Id
        WHERE Posts.User_Id = ?
        ORDER BY Date DESC
    """, (current_user.id,)).fetchall()

    comments = db.execute("""
        SELECT Comments.*, Users.Username as Username
        FROM Comments
        JOIN Users ON Comments.User_Id = Users.Id
        WHERE Comments.User_Id = ?
        ORDER BY Date DESC
    """, (current_user.id,)).fetchall()

    stats = db.execute(
        "SELECT TotalXP, CurrentLevel FROM UserStats WHERE UserId = ?",
        (current_user.id,)
    ).fetchone()

    xp = stats["TotalXP"] if stats else 0
    level = stats["CurrentLevel"] if stats else 1
    user_badge = badge(level)
    profile_user = {"Username": current_user.Username, "Role": current_user.Role}

    return render_template(
        "profile.html",
        posts=posts,
        comments=comments,
        profile_user=profile_user,
        report_count=0,
        is_own_profile=True,
        xp=xp,
        level=level,
        user_badge=user_badge,
    )


@main_bp.route("/profile/<username>")
@login_required
def user_profile(username):
    db = get_db()
    user_row = db.execute(
        "SELECT Id, Role, Ban_Status, Ban_Until FROM Users WHERE Username = ?",
        (username,),
    ).fetchone()

    if not user_row:
        flash("Utilisateur introuvable.")
        return redirect(url_for("main.index"))

    posts = db.execute("""
        SELECT Posts.*, Especes.Nom as Titre, Users.Username as Username
        FROM Posts
        LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
        JOIN Users ON Posts.User_Id = Users.Id
        WHERE Posts.User_Id = ?
        ORDER BY Date DESC
    """, (user_row["Id"],)).fetchall()

    comments = db.execute("""
        SELECT Comments.*, Users.Username as Username
        FROM Comments
        JOIN Users ON Comments.User_Id = Users.Id
        WHERE Comments.User_Id = ?
        ORDER BY Date DESC
    """, (user_row["Id"],)).fetchall()

    report_count = db.execute(
        "SELECT COUNT(*) FROM REPORT WHERE Reported_User_Id = ? OR post_id IN (SELECT Id FROM Posts WHERE User_Id = ?)",
        (user_row["Id"], user_row["Id"]),
    ).fetchone()[0]

    stats = db.execute(
        "SELECT TotalXP, CurrentLevel FROM UserStats WHERE UserId = ?",
        (user_row["Id"],),
    ).fetchone()

    xp = stats["TotalXP"] if stats else 0
    level = stats["CurrentLevel"] if stats else 1
    user_badge = badge(level)

    profile_user = {
        "Id": user_row["Id"],
        "Username": username,
        "Role": user_row["Role"],
        "Ban_Status": user_row["Ban_Status"],
        "Ban_Until": user_row["Ban_Until"],
    }

    return render_template(
        "profile.html",
        posts=posts,
        comments=comments,
        profile_user=profile_user,
        report_count=report_count,
        xp=xp,
        level=level,
        user_badge=user_badge,
        is_own_profile=(current_user.Username == username),
    )


@main_bp.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    contenu = request.form.get("Contenu")
    parent_id = request.form.get("Parent_Id") or None

    db = get_db()
    db.execute(
        "INSERT INTO Comments (Contenu, Date, User_Id, Post_Id, Parent_Id) VALUES (?, ?, ?, ?, ?)",
        (
            contenu,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_user.id,
            post_id,
            parent_id,
        ),
    )
    comment_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    log_action(
        db, current_user.id, "COMMENT_POSTED", comment_id, "comment", f"post:{post_id}"
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
    post = db.execute("""
        SELECT p.Id, e.Nom as Titre, p.Description, p.Localisation, p.Latitude, p.Longitude, p.Photo, u.Username as Username
        FROM Posts p
        JOIN Users u ON p.User_Id = u.Id
        LEFT JOIN Especes e ON p.Espece_Id = e.Id
        WHERE p.Id = ?
    """, (post_id,)).fetchone()

    if post is None:
        flash("Post introuvable.")
        return redirect(url_for("main.index"))

    if current_user.Username != post["Username"] and current_user.Role != "Admin":
        flash("Action non autorisée.")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        nouveau_nom = request.form.get("Titre")
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

        # Vérifier ou créer la nouvelle espèce
        espece = db.execute("SELECT Id FROM Especes WHERE Nom = ?", (nouveau_nom,)).fetchone()
        if espece:
            espece_id = espece["Id"]
        else:
            cursor = db.execute("INSERT INTO Especes (Nom) VALUES (?)", (nouveau_nom,))
            espece_id = cursor.lastrowid

        db.execute(
            "UPDATE Posts SET Espece_Id=?, Description=?, Localisation=?, Latitude=?, Longitude=?, Photo=? WHERE Id=?",
            (espece_id, description, localisation, latitude, longitude, filename, post_id),
        )
        log_action(db, current_user.id, "POST_EDITED", post_id, "post")
        db.commit()
        flash("Post modifié.")
        return redirect(url_for("main.index"))

    return render_template("publish.html", post=post)


@main_bp.route("/carte")
@login_required
def carte():
    db = get_db()
    query = """
        SELECT Posts.Id, Especes.Nom as Titre, Description, strftime('%Y-%m-%d', Date) as Date,
        Localisation, Latitude, Longitude, Users.Username as Username, Photo
        FROM Posts
        LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
        JOIN Users ON Posts.User_Id = Users.Id
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """
    if current_user.Role != "Admin":
        query += " AND (SELECT COUNT(*) FROM Report WHERE post_id = Posts.Id) < 3"
    posts = db.execute(query).fetchall()
    locations_list = db.execute(
        "SELECT DISTINCT Localisation FROM Posts ORDER BY Localisation"
    ).fetchall()
    return render_template(
        "map.html", posts=[dict(row) for row in posts], locations_list=locations_list
    )


@main_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    post = db.execute("""
        SELECT p.Id, u.Username as Username
        FROM Posts p
        JOIN Users u ON p.User_Id = u.Id
        WHERE p.Id = ?
    """, (post_id,)).fetchone()

    if post is None:
        flash("Post introuvable.")
        return redirect(url_for("main.index"))

    if current_user.Username != post["Username"] and current_user.Role != "Admin":
        flash("Action non autorisée.")
        return redirect(url_for("main.index"))

    # Les commentaires et reports liés sont supprimés automatiquement grâce au ON DELETE CASCADE de la table Posts
    db.execute("DELETE FROM Posts WHERE Id = ?", (post_id,))
    db.commit()
    flash("Post supprimé.")
    return redirect(url_for("main.index"))


@main_bp.route("/curation", methods=["GET", "POST"])
@login_required
def validation_post():
    if current_user.Role != "Biologiste":
        flash("Accès non autorisé.")
        return redirect(url_for("main.index"))
    db = get_db()

    if request.method == "POST":
        post_id = request.form.get("post_id")
        nouveau_nom = request.form.get("Titre")
        nouvelle_classe = request.form.get("Classe") # Le champ "Classe" doit exister dans ton formulaire HTML

        # Le biologiste vérifie l'espèce ou la corrige
        espece = db.execute("SELECT Id FROM Especes WHERE Nom = ?", (nouveau_nom,)).fetchone()
        if espece:
            # S'il ajoute une classe à une espèce existante
            if nouvelle_classe:
                db.execute("UPDATE Especes SET Classe = ? WHERE Id = ?", (nouvelle_classe, espece["Id"]))
            espece_id = espece["Id"]
        else:
            cursor = db.execute("INSERT INTO Especes (Nom, Classe) VALUES (?, ?)", (nouveau_nom, nouvelle_classe))
            espece_id = cursor.lastrowid

        db.execute(
            "UPDATE Posts SET Espece_Id = ? , is_verified = 1 WHERE Id = ?",
            (espece_id, post_id),
        )
        db.commit()
        flash(f"Post #{post_id} bien vérifié et espèce documentée.")

    query = """ SELECT Posts.Id, Especes.Nom as Titre, Description, strftime('%Y-%m-%d', Date) as Date,
                Localisation, Photo, is_verified
                FROM Posts
                LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
                WHERE is_verified = 0 ORDER BY Date DESC"""

    unverified_posts = db.execute(query).fetchall()
    return render_template("validation.html", posts=unverified_posts)


@main_bp.route("/report/post/<int:post_id>", methods=["POST"])
@login_required
def report_post(post_id):
    db = get_db()
    already = db.execute(
        "SELECT id FROM REPORT WHERE reporter_id = ? AND post_id = ?",
        (current_user.id, post_id),
    ).fetchone()
    if not already:
        db.execute(
            "INSERT INTO REPORT (reporter_id, post_id) VALUES (?, ?)",
            (current_user.id, post_id),
        )
        post = db.execute(
            "SELECT User_Id FROM Posts WHERE Id = ?", (post_id,)
        ).fetchone()
        if post:
            log_action(
                db,
                post["User_Id"],
                "REPORTED_BY",
                current_user.id,
                "user",
                f"par {current_user.Username} (post #{post_id})",
            )
        log_action(db, current_user.id, "REPORTED", post_id, "post")
        db.commit()
    return redirect(request.referrer)


@main_bp.route("/report/user/<int:user_id>", methods=["POST"])
@login_required
def report_user(user_id):
    db = get_db()
    already = db.execute(
        "SELECT id FROM REPORT WHERE reporter_id = ? AND Reported_User_Id = ?",
        (current_user.id, user_id),
    ).fetchone()
    if not already:
        db.execute(
            "INSERT INTO REPORT (reporter_id, Reported_User_Id) VALUES (?, ?)",
            (current_user.id, user_id),
        )
        log_action(
            db,
            user_id,
            "REPORTED_BY",
            current_user.id,
            "user",
            f"par {current_user.Username}",
        )
        log_action(db, current_user.id, "REPORTED", user_id, "user")
        db.commit()
    return redirect(request.referrer)


@main_bp.route("/admin/ban/<int:user_id>", methods=["POST"])
@login_required
def ban_user(user_id):
    ban_type = request.form.get("ban_type", "permanent")
    ban_until = request.form.get("ban_until")
    db = get_db()
    if ban_type == "temporary" and ban_until:
        db.execute(
            "UPDATE Users SET Ban_Status = 'temporary', Ban_Until = ? WHERE Id = ?",
            (ban_until, user_id),
        )
    else:
        db.execute(
            "UPDATE Users SET Ban_Status = 'permanent', Ban_Until = NULL WHERE Id = ?",
            (user_id,),
        )
    db.commit()
    return redirect(request.referrer)


@main_bp.route("/admin/unban/<int:user_id>", methods=["POST"])
@login_required
def unban_user(user_id):
    db = get_db()
    db.execute(
        "UPDATE Users SET Ban_Status = NULL, Ban_Until = NULL WHERE Id = ?", (user_id,)
    )
    db.commit()
    return redirect(request.referrer)


@main_bp.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    db = get_db()
    user = db.execute("SELECT Id FROM Users WHERE Id = ?", (user_id,)).fetchone()
    if user:
        # Grâce au CASCADE SQL, tous les Posts, Likes, Commentaires, Stats, Logs de l'utilisateur sont supprimés automatiquement
        db.execute("DELETE FROM Users WHERE Id = ?", (user_id,))
        db.commit()
    return redirect(url_for("main.index"))


@main_bp.route("/admin/logs/<int:user_id>")
@login_required
def user_logs(user_id):
    db = get_db()
    logs = db.execute(
        "SELECT * FROM UserLogs WHERE User_Id = ? ORDER BY Created_At DESC", (user_id,)
    ).fetchall()
    result = []
    for log in logs:
        result.append(dict(log))
    return jsonify(result)


@main_bp.route("/tableau")
@login_required
def tableau():
    db = get_db()

    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    sort_by = request.args.get('sort_by', 'Date')
    order = request.args.get('order', 'DESC').upper()

    valid_columns = {
        'Date': 'Date',
        'Espece': 'Especes.Nom',
        'Lieu': 'Localisation'
    }

    if sort_by not in valid_columns:
        sort_by = 'Date'
    if order not in ['ASC', 'DESC']:
        order = 'DESC'
    order_column = valid_columns[sort_by]

    # On utilise maintenant la table Especes pour afficher la Classe
    query = f"""
        SELECT Posts.Id, Especes.Nom as Espece, Especes.Classe,
               strftime('%Y-%m-%d', Date) as Date,
               Localisation, Users.Username as Username, Photo
        FROM Posts
        LEFT JOIN Especes ON Posts.Espece_Id = Especes.Id
        JOIN Users ON Posts.User_Id = Users.Id
        ORDER BY {order_column} {order}
        LIMIT ? OFFSET ?
    """
    posts = db.execute(query, (per_page, offset)).fetchall()

    total_posts = db.execute("SELECT COUNT(*) FROM Posts").fetchone()[0]
    total_pages = (total_posts + per_page - 1) // per_page
    next_order = 'ASC' if order == 'DESC' else 'DESC'

    return render_template(
        "tableau.html",
        posts=posts,
        page=page,
        total_pages=total_pages,
        sort_by=sort_by,
        order=order,
        next_order=next_order
    )


@main_bp.route("/graphs")
@login_required
def graphs():
    db = get_db()

    # 1. Répartition par Classe (Pie Chart)
    # Note : On compte les observations réelles liées aux espèces
    classe_dist = db.execute("""
        SELECT e.Classe, COUNT(p.Id) as count
        FROM Posts p
        JOIN Especes e ON p.Espece_Id = e.Id
        GROUP BY e.Classe
    """).fetchall()

    # 2. Évolution temporelle (Line Chart)
    post_growth = db.execute("""
        SELECT DATE(Date) as date, COUNT(Id) as count
        FROM Posts GROUP BY date ORDER BY date
    """).fetchall()

    # 3. Données pour l'inventaire et l'arbre
    # On récupère tout le catalogue (issu de ton Animaux.csv)
    species_raw = db.execute("SELECT Id, Nom, Parent_Id, Classe FROM Especes ORDER BY Nom").fetchall()
    all_species = [dict(row) for row in species_raw]

    return render_template("graphs.html",
                           classe_dist=classe_dist,
                           post_growth=post_growth,
                           all_species=all_species)
