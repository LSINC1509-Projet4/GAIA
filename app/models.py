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
    Role TEXT DEFAULT 'utilisateur',
    Ban_Status TEXT DEFAULT NULL,
    Ban_Until TIMESTAMP DEFAULT NULL
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
    Photo TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0
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

-- Table des Signalements
CREATE TABLE IF NOT EXISTS Report (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Reporter_Id INTEGER NOT NULL,
    Reported_User_Id INTEGER,
    Post_Id INTEGER,
    Comment_Id INTEGER,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Reporter_Id) REFERENCES Users(Id),
    FOREIGN KEY (Reported_User_Id) REFERENCES Users(Id),
    FOREIGN KEY (Post_Id) REFERENCES Posts(Id),
    FOREIGN KEY (Comment_Id) REFERENCES Comments(Id)
);

-- Table des Logs utilisateurs
CREATE TABLE IF NOT EXISTS UserLogs (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    User_Id INTEGER NOT NULL,
    Action_Type TEXT NOT NULL,
    Target_Id INTEGER,
    Target_Type TEXT,
    Detail TEXT,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_Id) REFERENCES Users(Id)
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
        is_verified,
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
        self.is_verified = is_verified


def init_db(db):
    """Exécute le schéma SQL pour créer les tables."""
    cursor = db.cursor()
    cursor.executescript(SCHEMA)
    db.commit()
