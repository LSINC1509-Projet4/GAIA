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
        filename = f"test_discovery_{int(datetime.now().timestamp())}.png"
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


if __name__ == "__main__":
    seed_file_post()
