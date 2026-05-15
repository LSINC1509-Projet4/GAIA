"""
Seed de données de test pour GAIA.

Crée un utilisateur biologiste + des observations sur de vraies espèces
du catalogue Animaux.csv (l'arbre de classification se construit
automatiquement via get_or_create_espece).

Pré-requis : la table Animaux doit déjà exister (lancer `python run.py` une
fois pour la créer, puis Ctrl+C, puis ce script).
"""
import sqlite3
from datetime import datetime, timedelta

from app.routes.main import get_or_create_espece

# Connexion à la base de données
conn = sqlite3.connect("gaia.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("🌱 Création des données de test...")

# ==========================================
# 1. UTILISATEUR DE TEST (biologiste)
# ==========================================
c.execute(
    "INSERT INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
    ("Darwin_Test", 50, "darwin@test.com", "1234", "Biologiste"),
)
id_user = c.lastrowid

# ==========================================
# 2. ESPÈCES — toutes prises du catalogue Animaux.csv
#    L'arbre de classification se construit automatiquement.
# ==========================================
ESPECES_TEST = [
    "Renard roux",
    "Loup arctique",
    "Loup gris",
    "Hermine",
    "Porc domestique",
]
ids_especes = {nom: get_or_create_espece(conn, nom) for nom in ESPECES_TEST}

# ==========================================
# 3. OBSERVATIONS étalées sur 5 jours (jolie courbe pour /graphs)
# ==========================================
now = datetime.now()
dates = [(now - timedelta(days=4 - i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(5)]

posts_data = [
    # J-4 : 1 post
    ("Observation rapide", dates[0], "Renard roux"),
    # J-3 : 2 posts
    ("Entendu dans la forêt", dates[1], "Loup gris"),
    ("Vu sur un rocher", dates[1], "Hermine"),
    # J-2 : 3 posts
    ("Empreintes trouvées", dates[2], "Loup arctique"),
    ("Près de la mare", dates[2], "Porc domestique"),
    ("Renard furtif", dates[2], "Renard roux"),
    # J-1 : 4 posts
    ("Loup posé sur l'arbre", dates[3], "Loup gris"),
    ("Hermine très rapide", dates[3], "Hermine"),
    ("Loup observé au loin", dates[3], "Loup arctique"),
    ("Cri de porc", dates[3], "Porc domestique"),
    # Aujourd'hui : 5 posts
    ("Magnifique renard !", dates[4], "Renard roux"),
    ("Loup proche de la rivière", dates[4], "Loup arctique"),
    ("Loup endormi", dates[4], "Loup gris"),
    ("Hermine cachée", dates[4], "Hermine"),
    ("Porc sauteur", dates[4], "Porc domestique"),
]

for desc, date, nom_espece in posts_data:
    c.execute(
        """
        INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude,
                           Photo, User_Id, Espece_Id, is_verified)
        VALUES (?, ?, ?, ?, ?, 'default.png', ?, ?, 1)
        """,
        (desc, date, "Forêt de Test", 50.8, 4.4, id_user, ids_especes[nom_espece]),
    )

conn.commit()
conn.close()

print(f"✅ {len(ESPECES_TEST)} espèces créées avec leur arbre, {len(posts_data)} observations.")
print("🚀 Relance ton serveur avec 'python run.py'")
