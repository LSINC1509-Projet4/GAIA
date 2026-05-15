# fichier tests
from app import create_app
from app.db import get_db
from app.models import init_db

app = create_app()

with app.app_context():
    db = get_db()

    # On crée les tables
    init_db(db)

    # On insère un utilisateur de test
    try:
        db.execute(
            "INSERT INTO Users (Username,Age, Email, Password) VALUES (?, ?, ?,?)",
            ("TestUser", 34, "test@gaia.com", "password123"),
        )
        db.commit()
    except Exception as e:
        print(f"Error")

    # On vérifie si on peut le lire
    user = db.execute(
        "SELECT * FROM users WHERE Username = ?", ("TestUser",)
    ).fetchone()
