import sqlite3

import pandas as pd
from flask import current_app, g

DATABASE = "gaia.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)

        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    db = get_db()
    df = pd.read_csv("Animaux.csv")
    df.to_sql("Animaux", db, if_exists="replace", index=False)
    print("Database initialized successfully.")


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
