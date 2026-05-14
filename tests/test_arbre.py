import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('gaia.db')
c = conn.cursor()

print("🌱 Plantation de l'arbre taxonomique et création des données...")

# ==========================================
# 1. L'ARBRE PHYLOGÉNÉTIQUE (Table Especes)
# ==========================================

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Le Vivant", "Racine", None))
id_racine = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Le Vivant",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Mammifères", "Mammifère", id_racine))
id_mam = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Mammifères",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Oiseaux", "Oiseau", id_racine))
id_ois = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Oiseaux",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Reptiles", "Reptile", id_racine))
id_rep = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Reptiles",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Amphibiens", "Amphibien", id_racine))
id_amp = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Amphibiens",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Renard roux", "Mammifère", id_mam))
id_renard = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Renard roux",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Ours brun", "Mammifère", id_mam))
id_ours = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Ours brun",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Chouette hulotte", "Oiseau", id_ois))
id_chouette = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Chouette hulotte",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Lézard des murailles", "Reptile", id_rep))
id_lezard = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Lézard des murailles",)).fetchone()[0]

c.execute("INSERT OR IGNORE INTO Especes (Nom, Classe, Parent_Id) VALUES (?, ?, ?)", ("Grenouille rousse", "Amphibien", id_amp))
id_grenouille = c.execute("SELECT Id FROM Especes WHERE Nom = ?", ("Grenouille rousse",)).fetchone()[0]

# ==========================================
# 2. UN UTILISATEUR DE TEST
# ==========================================
c.execute("INSERT OR IGNORE INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
          ("Darwin_Test", 50, "darwin@test.com", "1234", "Biologiste"))
id_user = c.execute("SELECT Id FROM Users WHERE Username = ?", ("Darwin_Test",)).fetchone()[0]

# ==========================================
# 3. GÉNÉRATION DE LA COURBE D'ÉVOLUTION
# ==========================================
now = datetime.now()

dates = [
    (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
    (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
    (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
    (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    now.strftime("%Y-%m-%d %H:%M:%S")
]

posts_data = [
    ("Observation rapide", dates[0], id_renard),
    ("Entendu dans la forêt", dates[1], id_chouette),
    ("Vu sur un rocher", dates[1], id_lezard),
    ("Empreintes trouvées", dates[2], id_ours),
    ("Près de la mare", dates[2], id_grenouille),
    ("Renard furtif", dates[2], id_renard),
    ("Chouette posée sur l'arbre", dates[3], id_chouette),
    ("Lézard très rapide", dates[3], id_lezard),
    ("Ours observé au loin", dates[3], id_ours),
    ("Chant de grenouille", dates[3], id_grenouille),
    ("Magnifique renard !", dates[4], id_renard),
    ("Ours proche de la rivière", dates[4], id_ours),
    ("Chouette endormie", dates[4], id_chouette),
    ("Lézard caché", dates[4], id_lezard),
    ("Grenouille sauteuse", dates[4], id_grenouille),
]

for desc, date, esp_id in posts_data:
    c.execute("""
        INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, Photo, User_Id, Espece_Id, is_verified)
        VALUES (?, ?, ?, ?, ?, 'default.png', ?, ?, 1)
    """, (desc, date, "Forêt de Test", 50.8, 4.4, id_user, esp_id))

conn.commit()
conn.close()

print("✅ Données de test générées avec succès !")
print("🚀 Relance ton serveur avec 'python run.py' et va sur http://127.0.0.1:5000/graphs")