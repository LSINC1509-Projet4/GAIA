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

-- Table des Niveaux Utilisateurs
CREATE TABLE IF NOT EXISTS UserStats (
    UserId INTEGER PRIMARY KEY AUTOINCREMENT,
    NbrePostsAlltime INTEGER DEFAULT 0,
    NBreLikesAlltime INTEGER DEFAULT 0,
    TotalXp REAL DEFAULT 0,
    CurrentLevel INTEGER DEFAULT 1,
    FOREIGN KEY (UserId) REFERENCES Users(Id)
);

-- Table des Likes
CREATE TABLE IF NOT EXISTS Likes (
    UserId INTEGER NOT NULL,
    PostId INTEGER NOT NULL,
    PRIMARY KEY (UserId, PostId),
    FOREIGN KEY (UserId) REFERENCES Users(Id),
    FOREIGN KEY (PostId) REFERENCES Posts(Id)
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
 -- Table signalements 
CREATE TABLE REPORT(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    post_id INTEGER,
    comment_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES Users(id),
    FOREIGN KEY (post_id) REFERENCES Posts(id),
    FOREIGN KEY (comment_id) REFERENCES Comments(id)
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
