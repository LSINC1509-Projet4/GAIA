from flask_login import UserMixin

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Age INT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    Password TEXT NOT NULL,
    Role TEXT DEFAULT 'utilisateur',
    Ban_Status TEXT DEFAULT NULL,
    Ban_Until TIMESTAMP DEFAULT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Especes (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Nom TEXT UNIQUE NOT NULL,
    NomScientifique TEXT,
    Classe TEXT,
    PhotoNaturaliste TEXT,
    Parent_Id INTEGER,
    FOREIGN KEY (Parent_Id) REFERENCES Especes(Id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Posts (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Description TEXT,
    Commentaire TEXT,
    Date TIMESTAMP NOT NULL,
    Localisation TEXT NOT NULL,
    Latitude REAL NOT NULL,
    Longitude REAL NOT NULL,
    Badges INTEGER,
    User_Id INTEGER NOT NULL,
    Espece_Id INTEGER,
    Photo TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0,
    TypePhoto TEXT DEFAULT 'observation',
    FOREIGN KEY (User_Id) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (Espece_Id) REFERENCES Especes(Id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS UserStats (
    UserId INTEGER PRIMARY KEY AUTOINCREMENT,
    NbrePostsAlltime INTEGER DEFAULT 0,
    NBreLikesAlltime INTEGER DEFAULT 0,
    TotalXp REAL DEFAULT 0,
    CurrentLevel INTEGER DEFAULT 1,
    FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Likes (
    UserId INTEGER NOT NULL,
    PostId INTEGER NOT NULL,
    PRIMARY KEY (UserId, PostId),
    FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (PostId) REFERENCES Posts(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Comments (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Contenu TEXT NOT NULL,
    Date TIMESTAMP NOT NULL,
    User_Id INTEGER NOT NULL,
    Post_Id INTEGER NOT NULL,
    Parent_Id INTEGER,
    FOREIGN KEY (User_Id) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (Post_Id) REFERENCES Posts(Id) ON DELETE CASCADE,
    FOREIGN KEY (Parent_Id) REFERENCES Comments(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Report (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Reporter_Id INTEGER NOT NULL,
    Reported_User_Id INTEGER,
    Post_Id INTEGER,
    Comment_Id INTEGER,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Reporter_Id) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (Reported_User_Id) REFERENCES Users(Id) ON DELETE CASCADE,
    FOREIGN KEY (Post_Id) REFERENCES Posts(Id) ON DELETE CASCADE,
    FOREIGN KEY (Comment_Id) REFERENCES Comments(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UserLogs (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    User_Id INTEGER NOT NULL,
    Action_Type TEXT NOT NULL,
    Target_Id INTEGER,
    Target_Type TEXT,
    Detail TEXT,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_Id) REFERENCES Users(Id) ON DELETE CASCADE
);
"""

class User(UserMixin):
    def __init__(self, Id, Username, Email, Role):
        self.id = Id
        self.Username = Username
        self.Email = Email
        self.Role = Role

class Post:
    def __init__(self, Id, Titre, Commentaires, Date, Localisation, Latitude, Longitude, Badges, User_Id, Photo, is_verified):
        self.id = Id
        self.Titre = Titre
        self.Date = Date
        self.Localisation = Localisation
        self.Latitude = Latitude
        self.Longitude = Longitude
        self.Badges = Badges
        self.User_Id = User_Id
        self.Photo = Photo
        self.is_verified = is_verified

def init_db(db):
    cursor = db.cursor()
    cursor.executescript(SCHEMA)
    db.commit()
