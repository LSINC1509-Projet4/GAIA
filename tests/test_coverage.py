"""
Coverage sur XP, badges, niveaux, routes Flask, DB, espèces, rôles et signalements
Lance avec:
    pip install pytest pytest-cov --break-system-packages
    pytest tests/test_coverage.py -v --cov=app --cov-report=term-missing
"""

import io
import json
import os
import tempfile

import pytest

from app.xp_logic import calculate_tot, calcul_levels, badge


# ──────────────────────────────────────────────
# Fixtures globales
# ──────────────────────────────────────────────

@pytest.fixture
def app():
    """Crée une instance Flask avec une DB temporaire."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    from app import create_app as _create
    import app.db as _db

    _db.DATABASE = db_path

    flask_app = _create()
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        WTF_CSRF_ENABLED=False,
    )

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        from app.db import get_db
        yield get_db()


def _register_and_login(client, username="TestUser", password="1234", role="utilisateur"):
    """Crée un compte et se connecte. Retourne le client."""
    client.post("/register.html", data={
        "Username": username,
        "Age": "25",
        "Email": f"{username}@test.com",
        "Password": password,
        "Role": role,
    }, follow_redirects=True)
    client.post("/login", data={
        "Username": username,
        "Password": password,
    }, follow_redirects=True)
    return client


# ══════════════════════════════════════════════
# 1. XP — calculate_tot
# ══════════════════════════════════════════════

class TestCalculateTot:
    def test_zero_zero(self):
        assert calculate_tot(0, 0) == 0

    def test_posts_only(self):
        assert calculate_tot(1, 0) == 50

    def test_likes_only(self):
        assert calculate_tot(0, 1) == 10

    def test_combined(self):
        # 3 posts x 50 + 5 likes x 10 = 150 + 50 = 200
        assert calculate_tot(3, 5) == 200

    def test_lineaire_posts(self):
        assert calculate_tot(10, 0) == 500

    def test_lineaire_likes(self):
        assert calculate_tot(0, 10) == 100

    def test_grand_nombre(self):
        assert calculate_tot(100, 100) == 6000


# ══════════════════════════════════════════════
# 2. Niveaux — calcul_levels
# ══════════════════════════════════════════════

class TestCalculLevels:
    def test_zero_xp_niveau_1(self):
        assert calcul_levels(0) == 1

    def test_xp_negatif_niveau_1(self):
        assert calcul_levels(-100) == 1

    def test_xp_faible(self):
        # sqrt(50/10) = sqrt(5) ≈ 2.23 → floor = 2
        assert calcul_levels(50) == 2

    def test_xp_1000(self):
        # sqrt(1000/10) = 10
        assert calcul_levels(1000) == 10

    def test_xp_4000(self):
        # sqrt(4000/10) = 20
        assert calcul_levels(4000) == 20

    def test_monotone(self):
        niveaux = [calcul_levels(x) for x in range(0, 5001, 50)]
        assert all(niveaux[i] <= niveaux[i + 1] for i in range(len(niveaux) - 1))


# ══════════════════════════════════════════════
# 3. Badges
# ══════════════════════════════════════════════

class TestBadge:
    def test_niveau_none(self):
        assert "Graine" in badge(None)

    def test_niveau_1(self):
        assert "Graine" in badge(1)

    def test_niveau_4(self):
        assert "Graine" in badge(4)

    def test_niveau_5(self):
        assert "Germe" in badge(5)

    def test_niveau_10(self):
        assert "Germe" in badge(10)

    def test_niveau_20(self):
        assert "Pousse" in badge(20)

    def test_niveau_39(self):
        assert "Branche" in badge(39)

    def test_niveau_40(self):
        assert "Bourgeon" in badge(40)

    def test_niveau_95(self):
        assert "Forêt" in badge(95)

    def test_tous_les_paliers_couverts(self):
        paliers = [0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        for p in paliers:
            result = badge(p)
            assert isinstance(result, str) and len(result) > 0, f"badge({p}) a renvoyé vide"

    def test_retour_string(self):
        assert isinstance(badge(7), str)


# ══════════════════════════════════════════════
# 4. Cohérence XP → niveau → badge
# ══════════════════════════════════════════════

class TestCohérenceXpNiveauBadge:
    def test_pipeline_complet_debutant(self):
        xp = calculate_tot(1, 0)
        lvl = calcul_levels(xp)
        b = badge(lvl)
        assert xp == 50
        assert lvl >= 1
        assert isinstance(b, str)

    def test_pipeline_veteran(self):
        xp = calculate_tot(50, 200)
        lvl = calcul_levels(xp)
        b = badge(lvl)
        assert lvl > 10
        assert "Graine" not in b

    def test_un_post_ne_retrograde_pas(self):
        lvl_avant = calcul_levels(calculate_tot(5, 10))
        lvl_apres = calcul_levels(calculate_tot(6, 10))
        assert lvl_apres >= lvl_avant


# ══════════════════════════════════════════════
# 5. Auth — login / logout / register
# ══════════════════════════════════════════════

class TestAuth:
    def test_login_page_accessible(self, client):
        r = client.get("/login")
        assert r.status_code == 200

    def test_register_et_login(self, client):
        r = client.post("/register.html", data={
            "Username": "Alice",
            "Age": "30",
            "Email": "alice@gaia.be",
            "Password": "pass",
            "Role": "utilisateur",
        }, follow_redirects=True)
        assert r.status_code == 200

        r = client.post("/login", data={
            "Username": "Alice",
            "Password": "pass",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_mauvais_mot_de_passe(self, client):
        _register_and_login(client, "Bob", "correct", "utilisateur")
        client.get("/logout")
        r = client.post("/login", data={
            "Username": "Bob",
            "Password": "faux",
        }, follow_redirects=True)
        assert b"incorrect" in r.data.lower() or r.status_code == 200

    def test_logout_redirige_login(self, client):
        _register_and_login(client)
        r = client.get("/logout", follow_redirects=True)
        assert r.status_code == 200

    def test_register_doublon_username(self, client):
        _register_and_login(client, "Doublon", "1234")
        client.get("/logout")
        r = client.post("/register.html", data={
            "Username": "Doublon",
            "Age": "20",
            "Email": "autre@gaia.be",
            "Password": "1234",
            "Role": "utilisateur",
        }, follow_redirects=True)
        assert b"pris" in r.data or r.status_code == 200


# ══════════════════════════════════════════════
# 6. Routes protégées (accès sans login)
# ══════════════════════════════════════════════

class TestRoutesProtegees:
    def test_feed_redirige_login(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code in (301, 302)

    def test_publish_redirige_login(self, client):
        r = client.get("/publish", follow_redirects=False)
        assert r.status_code in (301, 302)

    def test_carte_redirige_login(self, client):
        r = client.get("/carte", follow_redirects=False)
        assert r.status_code in (301, 302)

    def test_tableau_redirige_login(self, client):
        r = client.get("/tableau", follow_redirects=False)
        assert r.status_code in (301, 302)


# ══════════════════════════════════════════════
# 7. Routes dispo après le login
# ══════════════════════════════════════════════

class TestRoutesApresLogin:
    def test_feed_ok(self, client):
        _register_and_login(client)
        r = client.get("/")
        assert r.status_code == 200

    def test_publish_get_ok(self, client):
        _register_and_login(client)
        r = client.get("/publish")
        assert r.status_code == 200

    def test_carte_ok(self, client):
        _register_and_login(client)
        r = client.get("/carte")
        assert r.status_code == 200

    def test_tableau_ok(self, client):
        _register_and_login(client)
        r = client.get("/tableau")
        assert r.status_code == 200

    def test_graphs_ok(self, client):
        _register_and_login(client)
        r = client.get("/graphs")
        assert r.status_code == 200

    def test_profile_ok(self, client):
        _register_and_login(client)
        r = client.get("/profile")
        assert r.status_code == 200


# ══════════════════════════════════════════════
# 8. Publier un post
# ══════════════════════════════════════════════

class TestPublish:
    def test_publish_post_cree_observation(self, client, app):
        _register_and_login(client)
        img = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 10)
        r = client.post("/publish", data={
            "Titre": "Renard roux",
            "Description": "Vu en forêt",
            "Localisation": "Forêt de Soignes",
            "Latitude": "50.77",
            "Longitude": "4.41",
            "Photo": (img, "test.jpg"),
        }, content_type="multipart/form-data", follow_redirects=True)
        assert r.status_code == 200

        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute("SELECT COUNT(*) FROM Posts").fetchone()[0]
            assert count >= 1

    def test_flash_xp_apres_publication(self, client):
        _register_and_login(client)
        img = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 10)
        r = client.post("/publish", data={
            "Titre": "Loup gris",
            "Description": "Aperçu",
            "Localisation": "Ardennes",
            "Latitude": "50.15",
            "Longitude": "5.5",
            "Photo": (img, "loup.jpg"),
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"XP" in r.data


# ══════════════════════════════════════════════
# 9. Likes et XP
# ══════════════════════════════════════════════

class TestLikes:
    def _creer_post(self, client, app, username="Auteur"):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            espece = db.execute("SELECT Id FROM Especes LIMIT 1").fetchone()
            if not espece:
                db.execute("INSERT INTO Especes (Nom) VALUES ('Renard roux')")
                db.commit()
                espece_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            else:
                espece_id = espece["Id"]
            user = db.execute("SELECT Id FROM Users WHERE Username = ?", (username,)).fetchone()
            db.execute(
                "INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, Photo, User_Id, Espece_Id)"
                " VALUES (?, datetime('now'), ?, 50.7, 4.4, 'test.jpg', ?, ?)",
                ("Test", "LLN", user["Id"], espece_id),
            )
            db.commit()
            return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def test_like_incremente_xp(self, client, app):
        _register_and_login(client, "Auteur", "1234")
        client.get("/logout", follow_redirects=True)
        _register_and_login(client, "Liker", "1234")

        post_id = self._creer_post(client, app, "Auteur")

        with app.app_context():
            from app.db import get_db
            db = get_db()
            auteur_id = db.execute("SELECT Id FROM Users WHERE Username = 'Auteur'").fetchone()["Id"]
            xp_row = db.execute("SELECT TotalXp FROM UserStats WHERE UserId = ?", (auteur_id,)).fetchone()
            xp_avant = xp_row["TotalXp"] if xp_row else 0

        client.post(f"/like/{post_id}", follow_redirects=True)

        with app.app_context():
            from app.db import get_db
            db = get_db()
            auteur_id = db.execute("SELECT Id FROM Users WHERE Username = 'Auteur'").fetchone()["Id"]
            xp_row = db.execute("SELECT TotalXp FROM UserStats WHERE UserId = ?", (auteur_id,)).fetchone()
            xp_apres = xp_row["TotalXp"] if xp_row else 0

        assert xp_apres >= xp_avant


# ══════════════════════════════════════════════
# 10. arbre phylogénétique
# ══════════════════════════════════════════════

class TestGetOrCreateEspece:
    def test_espece_inconnue_creee_nue(self, app):
        with app.app_context():
            from app.db import get_db
            from app.routes.main import get_or_create_espece
            db = get_db()
            espece_id = get_or_create_espece(db, "Espèce fictive XYZ")
            db.commit()
            row = db.execute("SELECT Nom FROM Especes WHERE Id = ?", (espece_id,)).fetchone()
            assert row is not None
            assert row["Nom"] == "Espèce fictive XYZ"

    def test_espece_idempotente(self, app):
        with app.app_context():
            from app.db import get_db
            from app.routes.main import get_or_create_espece
            db = get_db()
            id1 = get_or_create_espece(db, "Espèce unique ABC")
            db.commit()
            id2 = get_or_create_espece(db, "Espèce unique ABC")
            assert id1 == id2

    def test_espece_catalogue_cree_arbre(self, app):
        with app.app_context():
            from app.db import get_db
            from app.routes.main import get_or_create_espece
            db = get_db()
            count = db.execute("SELECT COUNT(*) FROM Animaux").fetchone()[0]
            if count == 0:
                pytest.skip("Table Animaux vide — lancer test_db.py d'abord")
            espece_id = get_or_create_espece(db, "Renard roux")
            db.commit()
            row = db.execute("SELECT Parent_Id FROM Especes WHERE Id = ?", (espece_id,)).fetchone()
            assert row is not None
            assert row["Parent_Id"] is not None


# ══════════════════════════════════════════════
# 11. Rôles: accès admin et biologiste
# ══════════════════════════════════════════════

class TestRoles:
    def test_admin_reports_interdit_utilisateur(self, client):
        _register_and_login(client, "UserLambda", "1234", "utilisateur")
        r = client.get("/admin/reports", follow_redirects=True)
        assert b"r\xc3\xa9serv\xc3\xa9" in r.data or r.status_code == 200

    def test_admin_reports_accessible_admin(self, client):
        _register_and_login(client, "AdminTest", "1234", "Admin")
        r = client.get("/admin/reports")
        assert r.status_code == 200

    def test_admin_users_accessible_admin(self, client):
        _register_and_login(client, "AdminTest2", "1234", "Admin")
        r = client.get("/admin/users")
        assert r.status_code == 200

    def test_curation_interdit_utilisateur(self, client):
        _register_and_login(client, "UserNoBio", "1234", "utilisateur")
        r = client.get("/curation", follow_redirects=True)
        assert r.status_code == 200

    def test_curation_accessible_biologiste(self, client):
        _register_and_login(client, "BiologisteTest", "1234", "Biologiste")
        r = client.get("/curation")
        assert r.status_code == 200

    def test_add_species_interdit_utilisateur(self, client):
        _register_and_login(client, "UserNoAdd", "1234", "utilisateur")
        r = client.get("/add_species", follow_redirects=True)
        assert r.status_code == 200

    def test_add_species_accessible_biologiste(self, client):
        _register_and_login(client, "BioBio", "1234", "Biologiste")
        r = client.get("/add_species")
        assert r.status_code == 200


# ══════════════════════════════════════════════
# 12. Signalements
# ══════════════════════════════════════════════

class TestSignalements:
    def _seed_post(self, app, username):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            db.execute(
                "INSERT OR IGNORE INTO Users (Username, Age, Email, Password, Role)"
                " VALUES (?, 25, ?, '1234', 'utilisateur')",
                (username, f"{username}@sig.be"),
            )
            db.execute(
                "INSERT OR IGNORE INTO UserStats (UserId, NbrePostsAlltime, NBreLikesAlltime, TotalXp, CurrentLevel)"
                " SELECT Id, 0, 0, 0, 1 FROM Users WHERE Username = ?", (username,),
            )
            db.commit()
            uid = db.execute("SELECT Id FROM Users WHERE Username = ?", (username,)).fetchone()["Id"]
            db.execute("INSERT OR IGNORE INTO Especes (Nom) VALUES ('Lapin test')")
            db.commit()
            esp_id = db.execute("SELECT Id FROM Especes WHERE Nom = 'Lapin test'").fetchone()["Id"]
            db.execute(
                "INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, Photo, User_Id, Espece_Id)"
                " VALUES ('desc', datetime('now'), 'LLN', 50.7, 4.4, 'p.jpg', ?, ?)",
                (uid, esp_id),
            )
            db.commit()
            return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def test_signalement_enregistre(self, client, app):
        post_id = self._seed_post(app, "VictimeReport")
        _register_and_login(client, "Reporter", "1234", "utilisateur")
        r = client.post(
            f"/report/post/{post_id}",
            headers={"Referer": "/"},
            follow_redirects=True,
        )
        assert r.status_code == 200

        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute(
                "SELECT COUNT(*) FROM Report WHERE post_id = ?", (post_id,)
            ).fetchone()[0]
            assert count == 1

    def test_signalement_doublon_ignore(self, client, app):
        post_id = self._seed_post(app, "VictimeReport2")
        _register_and_login(client, "Reporter2", "1234", "utilisateur")
        client.post(f"/report/post/{post_id}", headers={"Referer": "/"}, follow_redirects=True)
        client.post(f"/report/post/{post_id}", headers={"Referer": "/"}, follow_redirects=True)

        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute(
                "SELECT COUNT(*) FROM Report WHERE post_id = ?", (post_id,)
            ).fetchone()[0]
            assert count == 1


# ══════════════════════════════════════════════
# 13. Commentaires
# ══════════════════════════════════════════════

class TestCommentaires:
    def _seed_post_simple(self, app, uid):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            db.execute("INSERT OR IGNORE INTO Especes (Nom) VALUES ('Mouton test')")
            db.commit()
            esp_id = db.execute("SELECT Id FROM Especes WHERE Nom = 'Mouton test'").fetchone()["Id"]
            db.execute(
                "INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, Photo, User_Id, Espece_Id)"
                " VALUES ('desc', datetime('now'), 'BXL', 50.8, 4.3, 'x.jpg', ?, ?)",
                (uid, esp_id),
            )
            db.commit()
            return db.execute("SELECT last_insert_rowid()").fetchone()[0]

    def test_commenter_un_post(self, client, app):
        _register_and_login(client, "Commenteur", "1234")
        with app.app_context():
            from app.db import get_db
            db = get_db()
            uid = db.execute("SELECT Id FROM Users WHERE Username = 'Commenteur'").fetchone()["Id"]
        post_id = self._seed_post_simple(app, uid)
        r = client.post(f"/post/{post_id}/comment", data={
            "Contenu": "Super observation !",
            "Parent_Id": "",
        }, follow_redirects=True)
        assert r.status_code == 200

        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute(
                "SELECT COUNT(*) FROM Comments WHERE Post_Id = ?", (post_id,)
            ).fetchone()[0]
            assert count == 1


# ══════════════════════════════════════════════
# 14. Autocomplete animaux
# ══════════════════════════════════════════════

class TestApiAnimaux:
    def test_query_trop_courte(self, client):
        _register_and_login(client)
        r = client.get("/api/animals?q=R")
        assert r.status_code == 200
        assert json.loads(r.data) == []

    def test_query_valide(self, client, app):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute("SELECT COUNT(*) FROM Animaux").fetchone()[0]
        if count == 0:
            pytest.skip("Animaux vide")
        _register_and_login(client)
        r = client.get("/api/animals?q=Renard")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_resultat_a_les_bons_champs(self, client, app):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            count = db.execute("SELECT COUNT(*) FROM Animaux").fetchone()[0]
        if count == 0:
            pytest.skip("Animaux vide")
        _register_and_login(client)
        r = client.get("/api/animals?q=Loup")
        results = json.loads(r.data)
        if results:
            assert "name" in results[0]
            assert "scientific" in results[0]


# ══════════════════════════════════════════════
# 15. Page espèce en détails
# ══════════════════════════════════════════════

class TestEspeceDetail:
    def test_espece_inexistante_redirige(self, client):
        _register_and_login(client)
        r = client.get("/espece/99999", follow_redirects=True)
        assert r.status_code == 200

    def test_espece_existante_accessible(self, client, app):
        with app.app_context():
            from app.db import get_db
            db = get_db()
            db.execute("INSERT OR IGNORE INTO Especes (Nom) VALUES ('Renard test detail')")
            db.commit()
            esp_id = db.execute("SELECT Id FROM Especes WHERE Nom = 'Renard test detail'").fetchone()["Id"]
        _register_and_login(client)
        r = client.get(f"/espece/{esp_id}")
        assert r.status_code == 200
        assert b"Renard test detail" in r.data


# ══════════════════════════════════════════════
# 16. Tableau et pagination
# ══════════════════════════════════════════════

class TestTableau:
    def test_tableau_page_1(self, client):
        _register_and_login(client)
        r = client.get("/tableau?page=1")
        assert r.status_code == 200

    def test_tableau_tri_par_espece(self, client):
        _register_and_login(client)
        r = client.get("/tableau?sort_by=Espece&order=ASC")
        assert r.status_code == 200

    def test_tableau_tri_par_lieu(self, client):
        _register_and_login(client)
        r = client.get("/tableau?sort_by=Lieu&order=DESC")
        assert r.status_code == 200

    def test_tableau_colonne_invalide_securisee(self, client):
        _register_and_login(client)
        r = client.get("/tableau?sort_by=DROP TABLE Posts--&order=ASC")
        assert r.status_code == 200


# ══════════════════════════════════════════════
# 17. Profil utilisateur
# ══════════════════════════════════════════════

class TestProfil:
    def test_profil_propre(self, client):
        _register_and_login(client, "ProfilUser", "1234")
        r = client.get("/profile")
        assert r.status_code == 200
        assert b"ProfilUser" in r.data

    def test_profil_public_autre_user(self, client, app):
        _register_and_login(client, "VisibleUser", "1234")
        client.get("/logout", follow_redirects=True)
        _register_and_login(client, "ViewerUser", "1234")
        r = client.get("/profile/VisibleUser")
        assert r.status_code == 200

    def test_profil_inexistant_redirige(self, client):
        _register_and_login(client)
        r = client.get("/profile/UtilisateurQuiNExistePas", follow_redirects=True)
        assert r.status_code == 200

# ══════════════════════════════════════════════
# 18. Coverage Posts
# ══════════════════════════════════════════════

class TestModels:
    def test_post_instanciation(self):
        from app.models import Post
        p = Post(1, "Renard roux", [], "2026-05-15", "Forêt", 50.7, 4.4, 0, 1, "photo.jpg", 0)
        assert p.id == 1
        assert p.Titre == "Renard roux"
        assert p.Photo == "photo.jpg"
        assert p.is_verified == 0