import re
import sqlite3
import unicodedata

import pandas as pd
from flask import current_app, g

DATABASE = "gaia.db"


def _normalize_column(name):
    """Translitère un nom de colonne en ASCII pur (sans accents, ni espaces).

    Ex: "Règne" -> "Regne", "Nom de l'animal" -> "Nom_de_l_animal".
    Évite tout problème d'encodage lors des requêtes sur la table Animaux.
    """
    sans_accents = "".join(
        c
        for c in unicodedata.normalize("NFKD", name)
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^0-9a-zA-Z]+", "_", sans_accents).strip("_")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)

        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = get_db()
    # Le CSV est encodé en UTF-8.
    df = pd.read_csv("Animaux.csv", encoding="utf-8")
    # Noms de colonnes translitérés en ASCII pur (Règne -> Regne) pour des
    # requêtes fiables, sans dépendre de l'encodage du terminal/de la DB.
    df.columns = [_normalize_column(c) for c in df.columns]
    df.to_sql("Animaux", db, if_exists="replace", index=False)
    print("Database initialized successfully.")


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
