from flask_login import UserMixin

SCHEMA = """
-- Désactiver les contraintes pour la création (optionnel)
PRAGMA foreign_keys = ON;

-- Table des Utilisateurs
CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Age INT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Role TEXT DEFAULT 'utilisateur'
);
"""


class User(UserMixin):
    def __init__(self, Id, Username, Email, Role):
        self.Id = Id
        self.Username = Username
        self.Email = Email
        self.Role = Role


def init_db(db):
    """Exécute le schéma SQL pour créer les tables."""
    cursor = db.cursor()
    cursor.executescript(SCHEMA)
    db.commit()
