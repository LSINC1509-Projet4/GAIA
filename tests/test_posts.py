import os
import shutil
from datetime import datetime

from app import create_app
from app.db import get_db


def seed_file_post():
    app = create_app()

    with app.app_context():
        db = get_db()

        # 1. Define paths
        source_image = "app/static/panda.png"  # Using your logo as a test image
        upload_folder = "app/static/uploads"
        filename = "test_panda.png"
        target_path = os.path.join(upload_folder, filename)

        # 2. Ensure the upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"Created folder: {upload_folder}")

        # 3. Simulate "saving" a file by copying it
        try:
            shutil.copy(source_image, target_path)
            print(f"Image copied to: {target_path}")
        except FileNotFoundError:
            print("Error: source image 'app/static/Logo.png' not found.")
            return

        # 4. Insert into DB (Saving the STRING path, not the BLOB)
        try:
            db.execute(
                """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Badges, Username, Photo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ? )""",
                (
                    "MY PANDA",
                    "MY FAVORITE",
                    "CUTE.",
                    datetime.now().strftime("%Y-%m-%d"),
                    "MONS",
                    50.585,
                    3.887,
                    10,
                    "TestUser",
                    filename,  # This is the string (e.g., 'test_discovery_1776288311.png')
                ),
            )
            db.commit()
            print("Database updated with photo reference!")
        except Exception as e:
            print(f"Error: {e}")

        # =========================
        # POST 2 : RENARD ROUX
        # =========================
        source_image = "app/static/renard.png"
        filename = "test_renard.png"
        target_path = os.path.join(upload_folder, filename)

        try:
            shutil.copy(source_image, target_path)
            print(f"Image copied to: {target_path}")
        except FileNotFoundError:
            print(f"Error: source image '{source_image}' not found.")
            filename = None

        try:
            db.execute(
                """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Badges, Username, Photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ? )""",
                (
                    "Renard roux",
                    "Aperçu dans la forêt tôt le matin",
                    "Magnifique",
                    datetime.now().strftime("%Y-%m-%d"),
                    "Forêt de Soignes",
                    50.7700,
                    4.4100,
                    0,
                    "TestUser",
                    filename,
                ),
            )
            db.commit()
            print("Database updated with photo reference!")
        except Exception as e:
            print(f"Error: {e}")

        # =========================
        # POST 3 : CHOUETTE HULOTTE
        # =========================
        source_image = "app/static/chouette.png"
        filename = "test_chouette.png"
        target_path = os.path.join(upload_folder, filename)

        try:
            shutil.copy(source_image, target_path)
            print(f"Image copied to: {target_path}")
        except FileNotFoundError:
            print(f"Error: source image '{source_image}' not found.")
            filename = None

        try:
            db.execute(
                """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Badges, Username, Photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ? )""",
                (
                    "Chouette hulotte",
                    "Entendue la nuit dans un vieux chêne",
                    "Chant mystérieux",
                    datetime.now().strftime("%Y-%m-%d"),
                    "Ardennes",
                    50.1500,
                    5.5000,
                    0,
                    "TestUser",
                    filename,
                ),
            )
            db.commit()
            print("Database updated with photo reference!")
        except Exception as e:
            print(f"Error: {e}")

        # =========================
        # POST 4 : ÉCUREUIL ROUX
        # =========================
        source_image = "app/static/ecureuil.png"
        filename = "test_ecureil.png"
        target_path = os.path.join(upload_folder, filename)

        try:
            shutil.copy(source_image, target_path)
            print(f"Image copied to: {target_path}")
        except FileNotFoundError:
            print(f"Error: source image '{source_image}' not found.")
            filename = None

        try:
            db.execute(
                """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Badges, Username, Photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ? )""",
                (
                    "Écureuil roux",
                    "Grimpait à toute vitesse sur un pin",
                    "Trop rapide pour une photo nette",
                    datetime.now().strftime("%Y-%m-%d"),
                    "Parc de Bruxelles",
                    50.8450,
                    4.3650,
                    0,
                    "TestUser",
                    filename,
                ),
            )
            db.commit()
            print("Database updated with photo reference!")
        except Exception as e:
            print(f"Error: {e}")

        # =========================
        # POST 5 : CERF ÉLAPHE
        # =========================
        source_image = "app/static/cerf.png"
        filename = "test_cerf.png"
        target_path = os.path.join(upload_folder, filename)

        try:
            shutil.copy(source_image, target_path)
            print(f"Image copied to: {target_path}")
        except FileNotFoundError:
            print(f"Error: source image '{source_image}' not found.")
            filename = None

        try:
            db.execute(
                """INSERT INTO Posts (Titre, Description, Commentaire, Date, Localisation, Latitude, Longitude, Badges, Username, Photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? , ? )""",
                (
                    "Cerf élaphe",
                    "Troupeau observé au crépuscule",
                    "Impressionnant",
                    datetime.now().strftime("%Y-%m-%d"),
                    "Hautes Fagnes",
                    50.5000,
                    6.1000,
                    0,
                    "TestUser",
                    filename,
                ),
            )
            db.commit()
            print("Database updated with photo reference!")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    seed_file_post()
