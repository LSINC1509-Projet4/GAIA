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

-- Table des Posts
CREATE TABLE IF NOT EXISTS Posts (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Titre text NOT NULL ,
    Description TEXT,
    Commentaire TEXT ,
    Date TIMESTAMP NOT NULL,
    Localisation TEXT NOT NULL,
    Latitude REAL NOT NULL,
    Longitude REAL NOT NULL,
    Badges INTEGER ,
    Username TEXT NOT NULL,
    Photo TEXT NOT NULL
);

-- Table des Commentaires
CREATE TABLE IF NOT EXISTS Comments (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Contenu TEXT NOT NULL,
    Date TIMESTAMP NOT NULL,
    Username TEXT NOT NULL,
    Post_Id INTEGER NOT NULL,
    Parent_Id INTEGER,
    FOREIGN KEY (Post_Id) REFERENCES Posts(Id),
    FOREIGN KEY (Parent_Id) REFERENCES Comments(Id)
);
"""


class User(UserMixin):
    def __init__(self, Id, Username, Email, Role):
        self.id = Id
        self.Username = Username
        self.Email = Email
        self.Role = Role


class Post:
    def __init__(
        self,
        Id,
        Titre,
        Commentaires,
        Date,
        Localisation,
        Latitude,
        Longitude,
        Badges,
        Username,
        Photo,
    ):
        self.id = Id
        self.Titre = Titre
        self.Date = Date
        self.Localisation = Localisation
        self.Latitude = Latitude
        self.Longitude = Longitude
        self.Badges = Badges
        self.Username = Username
        self.Photo = Photo


def init_db(db):
    """Exécute le schéma SQL pour créer les tables."""
    cursor = db.cursor()
    cursor.executescript(SCHEMA)
    db.commit()
