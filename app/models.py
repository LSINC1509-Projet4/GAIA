from flask_login import UserMixin

SCHEMA = """
-- Désactiver les contraintes pour la création (optionnel)
PRAGMA foreign_keys = ON;

-- Table des Utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    Age INT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'utilisateur'
);
"""

class User(UserMixin):
    def __init__(self, id, username, email, role):
        self.id = id
        self.username = username
        self.email = email
        self.role = role

def init_db(db):
    """Exécute le schéma SQL pour créer les tables."""
    cursor = db.cursor()
    cursor.executescript(SCHEMA)
    db.commit()
