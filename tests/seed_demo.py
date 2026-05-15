"""
Seed de démo pour GAIA — remplit la base avec un état réaliste pour une présentation.

Crée :
- 8 utilisateurs (admin, biologistes, utilisateurs) avec mots de passe simples
- 25 espèces réelles du catalogue Animaux.csv (arbre de classification complet)
- ~80 observations étalées sur 30 jours, dans des vrais lieux belges
- des commentaires et des likes éparpillés
- 5 planches naturalistes (par les biologistes)

Pré-requis : la table Animaux doit déjà exister.
Lancer `python run.py` une fois (Ctrl+C), puis `python -m tests.seed_demo`.
"""
import os
import random
import re
import sqlite3
import sys
from datetime import datetime, timedelta

from app.routes.main import get_or_create_espece
from app.xp_logic import calcul_levels, calculate_tot

# Console Windows : force UTF-8 (sinon les ✔/✗ et accents crashent en cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

random.seed(42)

# --- Volumes du seed (gonfle/baisse ici pour ajuster) ---
NB_POSTS = 300
NB_COMMENTS = 150

SPECIES_PHOTO_DIR = os.path.join("app", "static", "uploads", "species")


def _photos_inat_pour(nom_espece):
    """Liste des chemins relatifs à uploads/ des photos iNat pour cette espèce."""
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", nom_espece).strip("_").lower()
    if not os.path.isdir(SPECIES_PHOTO_DIR):
        return []
    return [
        f"species/{f}" for f in os.listdir(SPECIES_PHOTO_DIR)
        if re.match(rf"^{re.escape(safe)}_\d+\.jpg$", f)
    ]


def a_des_photos_inat(nom_espece):
    """True si on a au moins une photo iNat téléchargée pour cette espèce."""
    return bool(_photos_inat_pour(nom_espece))


def photo_pour(nom_espece, fallback_pool):
    """Renvoie le chemin d'UNE photo de cette espèce, choisie au hasard.
    Tombe sur une photo de secours si pas de photo iNat."""
    candidats = _photos_inat_pour(nom_espece)
    if candidats:
        return random.choice(candidats)
    if fallback_pool:
        return random.choice(fallback_pool)
    return None  # pas censé arriver, on filtre les espèces sans photo en amont

conn = sqlite3.connect("gaia.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("Génération du seed de démo...")

# ==========================================
# 1. UTILISATEURS
# ==========================================
USERS = [
    # Personas du projet (cf. docs/PERSONAS/PERSONAS.md)
    # (Username, Age, Email, Password, Role)
    ("Root",                  35, "root@gaia.be",                "admin",       "Admin"),
    ("Dr_Hippo_Thalamus",     52, "hippo.thalamus@biogaia.be",   "biologiste",  "Biologiste"),
    ("Marc_Assin",            41, "marc.assin@biogaia.be",       "biologiste",  "Biologiste"),
    ("Nathan_Dendoncker",     37, "nathan.dendoncker@gmail.com", "user",        "utilisateur"),
    ("Anya_Delforger",        22, "anya.delforger@student.be",   "user",        "utilisateur"),
    ("Jonathan_Delneufcourt",  7, "jonathan.7ans@gmail.com",     "user",        "utilisateur"),
]
ids_users = {}
for username, age, email, pwd, role in USERS:
    try:
        c.execute(
            "INSERT INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
            (username, age, email, pwd, role),
        )
        uid = c.lastrowid
    except sqlite3.IntegrityError:
        uid = c.execute("SELECT Id FROM Users WHERE Username = ?", (username,)).fetchone()["Id"]
    ids_users[username] = uid
    # initialise les stats XP
    c.execute(
        "INSERT OR IGNORE INTO UserStats (UserId, NbrePostsAlltime, NBreLikesAlltime, TotalXp, CurrentLevel) "
        "VALUES (?, 0, 0, 0, 1)",
        (uid,),
    )
print(f"  ✔ {len(USERS)} utilisateurs créés")

# ==========================================
# 2. ESPÈCES (toutes du catalogue Animaux.csv)
# ==========================================
ESPECES = [
    "Renard roux", "Renard polaire", "Renard gris",
    "Loup gris", "Loup arctique", "Loup du Mexique",
    "Hermine", "Porc domestique",
    "Maki catta", "Galéopithèque de la Sonde", "Chlamydophore tronqué",
    "Éléphant d'Asie", "Éléphant de Sumatra", "Éléphant de Bornéo",
    "Écureuil roux américain", "Oryx d'Arabie", "Vache Highland",
    "Urial", "Quokka", "Fennec",
    "Tangue zébré", "Hyène brune",
    "Mara de Patagonie", "Antilope cervicapre",
    "Rhinopithèque de Roxellane",
]
ids_especes = {}
for nom in ESPECES:
    try:
        ids_especes[nom] = get_or_create_espece(conn, nom)
    except Exception as e:
        print(f"  ⚠ {nom!r} introuvable au catalogue : {e}")

# Garde uniquement celles qui ont marché ET qui ont au moins une photo iNat
ESPECES = [e for e in ESPECES if e in ids_especes and a_des_photos_inat(e)]
print(f"  ✔ {len(ESPECES)} espèces (avec arbre + photos iNat) prêtes")

# ==========================================
# 3. LIEUX par région biogéographique (cohérence avec l'espèce)
# ==========================================
REGIONS = {
    "Belgique": [
        ("Forêt de Soignes",                  50.7700, 4.4150),
        ("Hautes Fagnes",                     50.5000, 6.1000),
        ("Bois de la Cambre",                 50.8050, 4.3850),
        ("Vallée de la Lesse",                50.1500, 4.9500),
        ("Parc Naturel Viroin-Hermeton",      50.0700, 4.6500),
        ("Hertogenwald",                      50.5800, 6.0500),
        ("Marais d'Harchies",                 50.4700, 3.6850),
    ],
    "Arctique": [
        ("Spitzberg, Norvège",                78.2200, 15.6500),
        ("Île d'Ellesmere, Canada",           80.0000, -86.0000),
        ("Île Wrangel, Russie",               71.2300, -179.5000),
        ("Scoresby Sund, Groenland",          71.0000, -23.0000),
    ],
    "Sahara": [
        ("Erg Chebbi, Maroc",                 31.1500, -3.9667),
        ("Désert du Ténéré, Niger",           18.0000, 10.5000),
        ("Sahara tunisien, Douz",             33.4500, 9.0250),
    ],
    "Amérique du Nord": [
        ("Yellowstone, USA",                  44.6000, -110.5000),
        ("Désert de Sonora, Mexique",         29.5000, -111.0000),
        ("Algonquin Park, Canada",            45.8400, -78.4000),
        ("Sierra Madre, Mexique",             24.0000, -106.0000),
    ],
    "Madagascar": [
        ("Réserve d'Andasibe",                -18.9300, 48.4170),
        ("Parc National d'Isalo",             -22.5400, 45.3500),
        ("Forêt de Berenty",                  -25.0167, 46.3000),
    ],
    "Asie du Sud": [
        ("Parc national de Yala, Sri Lanka",   6.3725, 81.5176),
        ("Réserve de Périyar, Inde",           9.5916, 77.2424),
        ("Forêt de Sumatra, Indonésie",        0.0000, 102.0000),
        ("Parc de Sabah, Bornéo",              5.5000, 116.0000),
    ],
    "Australie": [
        ("Île de Rottnest, Australie",       -32.0000, 115.5000),
        ("Kakadu National Park",             -12.5000, 132.5000),
    ],
    "Amérique du Sud": [
        ("Pampa de Patagonie, Argentine",    -42.0000, -68.0000),
        ("Pantanal, Brésil",                 -17.0000, -57.0000),
    ],
    "Afrique australe": [
        ("Parc Etosha, Namibie",             -19.0000, 16.0000),
        ("Kruger Park, Afrique du Sud",      -23.9884, 31.5547),
        ("Désert du Kalahari, Botswana",     -23.0000, 22.0000),
    ],
    "Asie centrale": [
        ("Pamir, Tadjikistan",                38.5000, 73.0000),
        ("Plateau du Tibet, Chine",           33.0000, 88.0000),
        ("Steppes mongoles",                  47.0000, 105.0000),
    ],
    "Moyen-Orient": [
        ("Désert d'Arabie, Émirats",          24.0000, 54.0000),
        ("Réserve de Mahazat as-Sayd",        22.0000, 41.5000),
    ],
}

# Région d'origine (probable) de chaque espèce
ESPECE_REGION = {
    "Renard roux":               "Belgique",
    "Renard polaire":            "Arctique",
    "Renard gris":               "Amérique du Nord",
    "Fennec":                    "Sahara",
    "Loup gris":                 "Belgique",
    "Loup arctique":             "Arctique",
    "Loup du Mexique":           "Amérique du Nord",
    "Hermine":                   "Belgique",
    "Hyène brune":               "Afrique australe",
    "Maki catta":                "Madagascar",
    "Galéopithèque de la Sonde": "Asie du Sud",
    "Rhinopithèque de Roxellane":"Asie centrale",
    "Quokka":                    "Australie",
    "Mara de Patagonie":         "Amérique du Sud",
    "Éléphant d'Asie":           "Asie du Sud",
    "Éléphant de Sumatra":       "Asie du Sud",
    "Éléphant de Bornéo":        "Asie du Sud",
    "Oryx d'Arabie":             "Moyen-Orient",
    "Urial":                     "Asie centrale",
    "Antilope cervicapre":       "Asie du Sud",
    "Écureuil roux américain":   "Amérique du Nord",
    "Écureuil de Douglas":       "Amérique du Nord",
    "Porc domestique":           "Belgique",
    "Vache Highland":            "Belgique",
    "Chlamydophore tronqué":     "Amérique du Sud",
    "Tangue zébré":              "Madagascar",
}


def lieu_pour(nom_espece):
    """Renvoie un lieu plausible pour cette espèce (selon sa région)."""
    region = ESPECE_REGION.get(nom_espece, "Belgique")
    return random.choice(REGIONS[region])

PHOTOS_FALLBACK = []  # vide volontairement : on saute les espèces sans photo iNat

DESCRIPTIONS = [
    "Belle observation, individu en bonne santé.",
    "Aperçu rapide pendant l'excursion, comportement calme.",
    "Trace fraîche au sol, animal probablement à proximité.",
    "Vu à travers les jumelles, magnifique.",
    "Famille avec petits aperçue de loin.",
    "Belle rencontre, l'animal m'a regardé puis s'est éloigné.",
    "Empreintes nettes au sol, à confirmer.",
    "Activité plus marquée que d'habitude.",
    "Repéré durant la randonnée matinale.",
    "Individu observé près d'un point d'eau.",
    "Vu en groupe, comportement social typique.",
    "Pris en photo de loin pour ne pas perturber.",
]

# ==========================================
# 4. OBSERVATIONS — étalées sur 30 jours
# ==========================================
USERS_POSTANTS = [u for u in ids_users if u != "Root"]  # admin ne poste pas
now = datetime.now()

post_ids = []
for _ in range(NB_POSTS):
    user = random.choice(USERS_POSTANTS)
    espece = random.choice(ESPECES)
    lieu, lat, lng = lieu_pour(espece)
    # petit bruit autour du point pour éviter les pins parfaitement superposés
    lat += random.uniform(-0.05, 0.05)
    lng += random.uniform(-0.05, 0.05)
    desc = random.choice(DESCRIPTIONS)
    photo = photo_pour(espece, PHOTOS_FALLBACK)
    days_ago = random.randint(0, 29)
    hours_ago = random.randint(0, 23)
    date = (now - timedelta(days=days_ago, hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
    is_verified = 1 if random.random() < 0.7 else 0
    c.execute(
        """
        INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude,
                           Photo, User_Id, Espece_Id, is_verified, TypePhoto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'observation')
        """,
        (desc, date, lieu, lat, lng, photo, ids_users[user], ids_especes[espece], is_verified),
    )
    post_ids.append(c.lastrowid)
print(f"  ✔ {NB_POSTS} observations créées")

# ==========================================
# 5. PLANCHES NATURALISTES — par les biologistes
# ==========================================
# Les biologistes "officialisent" la moitié des espèces avec une planche
# (la photo de référence est la photo Wikipedia téléchargée)
biologistes = [u for u in ids_users if u in ("Dr_Hippo_Thalamus", "Marc_Assin")]
especes_naturalisees = random.sample(ESPECES, k=min(len(ESPECES) // 2, len(ESPECES)))
nb_planches = 0
for espece in especes_naturalisees:
    photo = photo_pour(espece, PHOTOS_FALLBACK)
    if not photo.startswith("species/"):
        continue  # pas de photo Wikipedia téléchargée -> on ne crée pas de planche
    username = random.choice(biologistes)
    date = (now - timedelta(days=random.randint(1, 25))).strftime("%Y-%m-%d %H:%M:%S")
    lieu, lat, lng = lieu_pour(espece)
    c.execute(
        """
        INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude,
                           Photo, User_Id, Espece_Id, is_verified, TypePhoto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'naturaliste')
        """,
        (f"Planche de référence — {espece}", date, lieu, lat, lng, photo,
         ids_users[username], ids_especes[espece]),
    )
    c.execute(
        "UPDATE Especes SET PhotoNaturaliste = ? WHERE Id = ?",
        (photo, ids_especes[espece]),
    )
    nb_planches += 1
print(f"  ✔ {nb_planches} planches naturalistes")

# ==========================================
# 6. COMMENTAIRES
# ==========================================
COMMS = [
    "Magnifique observation !", "Wow, j'aimerais bien en voir un un jour.",
    "Excellente photo, bravo.", "On voit ça de plus en plus dans la région.",
    "Tu as eu de la chance !", "Sympa de partager, merci.",
    "C'est rare d'en croiser, super spot.", "Belle prise.",
    "Tu peux préciser l'heure exacte ?", "On a vu la même chose la semaine passée."
]
nb_comments = 0
for _ in range(NB_COMMENTS):
    pid = random.choice(post_ids)
    user = random.choice(USERS_POSTANTS)
    contenu = random.choice(COMMS)
    days_ago = random.randint(0, 28)
    date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO Comments (Contenu, Date, User_Id, Post_Id) VALUES (?, ?, ?, ?)",
        (contenu, date, ids_users[user], pid),
    )
    nb_comments += 1
print(f"  ✔ {nb_comments} commentaires")

# ==========================================
# 7. LIKES
# ==========================================
nb_likes = 0
all_user_ids = list(ids_users.values())
for pid in post_ids:
    # 0 à 6 likes par post, sans doublons
    nb = random.randint(0, 6)
    likers = random.sample(all_user_ids, k=min(nb, len(all_user_ids)))
    for uid in likers:
        try:
            c.execute("INSERT INTO Likes (UserId, PostId) VALUES (?, ?)", (uid, pid))
            nb_likes += 1
        except sqlite3.IntegrityError:
            pass
print(f"  ✔ {nb_likes} likes")

# ==========================================
# 8. RECALCUL DES STATS XP
# ==========================================
for username, uid in ids_users.items():
    nb_posts = c.execute("SELECT COUNT(*) FROM Posts WHERE User_Id = ?", (uid,)).fetchone()[0]
    nb_likes_recus = c.execute(
        "SELECT COUNT(*) FROM Likes l JOIN Posts p ON l.PostId = p.Id WHERE p.User_Id = ?",
        (uid,),
    ).fetchone()[0]
    xp = calculate_tot(nb_posts, nb_likes_recus)
    lvl = calcul_levels(xp)
    c.execute(
        "UPDATE UserStats SET NbrePostsAlltime = ?, NBreLikesAlltime = ?, TotalXp = ?, CurrentLevel = ? "
        "WHERE UserId = ?",
        (nb_posts, nb_likes_recus, xp, lvl, uid),
    )
print(f"  ✔ Stats XP/niveau recalculées pour tous les users")

conn.commit()
conn.close()

print("\n✅ Seed de démo terminé. Comptes pour la présentation :")
for u in USERS:
    print(f"   • {u[0]:18} (mdp: {u[3]:12}) — rôle: {u[4]}")
print("\n🚀 Relance 'python run.py'")
