#fichier tests 
from app import create_app
from app.db import get_db
from app.models import init_db

app = create_app()

with app.app_context():
    db = get_db()
    
    #On crée les tables
    print("Construction des tables...")
    init_db(db)
    
    # On insère un utilisateur de test
    try:
        db.execute(
            "INSERT INTO users (username,Age, email, password) VALUES (?, ?, ?,?)",
            ("TestUser", 34, "test@gaia.com", "password123")
        )
        db.commit()
        print("✅ Utilisateur inséré avec succès !")
    except Exception as e:
        print(f"❌ Erreur d'insertion (peut-être qu'il existe déjà ?) : {e}")

    # On vérifie si on peut le lire
    user = db.execute("SELECT * FROM users WHERE username = ?", ("TestUser",)).fetchone()
    
    if user:
        print(f"🔍 Lecture réussie ! ID: {user['id']}, Pseudo: {user['username']}")
    else:
        print("❌ Impossible de retrouver l'utilisateur.")