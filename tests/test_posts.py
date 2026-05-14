import os
import shutil
from datetime import datetime
from app import create_app
from app.db import get_db

def seed_file_post():
    app = create_app()

    with app.app_context():
        db = get_db()
        upload_folder = "app/static/uploads"

        # 1. S'assurer que le dossier uploads existe
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"📁 Dossier créé : {upload_folder}")

        # 2. Récupérer l'ID de l'utilisateur de test (Admin_Gaia ou TestUser)
        # On essaie de trouver 'TestUser', sinon on prend le premier utilisateur trouvé
        user = db.execute("SELECT Id FROM Users WHERE Username = ?", ("TestUser",)).fetchone()
        if not user:
            # Si TestUser n'existe pas, on le crée vite fait pour le test
            db.execute("INSERT INTO Users (Username, Age, Email, Password, Role) VALUES (?, ?, ?, ?, ?)",
                      ("TestUser", 25, "test@gaia.com", "1234", "utilisateur"))
            db.commit()
            user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            user_id = user['Id']

        # 3. Liste des données à insérer
        # Structure : (Nom_Espece, Description, Localisation, Lat, Long, Image_Source)
        data_to_seed = [
            ("Panda", "Mon panda préféré", "Mons", 50.585, 3.887, "panda.png"),
            ("Renard roux", "Aperçu dans la forêt tôt le matin", "Forêt de Soignes", 50.7700, 4.4100, "renard.png"),
            ("Chouette hulotte", "Entendue la nuit dans un vieux chêne", "Ardennes", 50.1500, 5.5000, "chouette.png"),
            ("Écureuil roux", "Grimpait à toute vitesse", "Parc de Bruxelles", 50.8450, 4.3650, "ecureuil.png"),
            ("Cerf élaphe", "Troupeau observé au crépuscule", "Hautes Fagnes", 50.5000, 6.1000, "cerf.png")
        ]

        for nom_esp, desc, loc, lat, lon, img_src in data_to_seed:
            # A. Chercher l'ID de l'espèce (Normalisation)
            espece = db.execute("SELECT Id FROM Especes WHERE Nom LIKE ?", (f"%{nom_esp}%",)).fetchone()

            if not espece:
                print(f"⚠️ L'espèce '{nom_esp}' n'existe pas dans ton CSV. On l'ajoute à la volée.")
                db.execute("INSERT INTO Especes (Nom, Classe) VALUES (?, ?)", (nom_esp, "Inconnu"))
                espece_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            else:
                espece_id = espece['Id']

            # B. Gérer l'image
            src_path = os.path.join("app/static", img_src)
            filename = f"test_{img_src}"
            target_path = os.path.join(upload_folder, filename)

            if os.path.exists(src_path):
                shutil.copy(src_path, target_path)
                print(f"📸 Image copiée : {filename}")
            else:
                print(f"❌ Image source introuvable : {src_path}")
                filename = "default.png" # Fallback

            # C. Insertion du Post
            try:
                db.execute(
                    """INSERT INTO Posts (Description, Date, Localisation, Latitude, Longitude, User_Id, Espece_Id, Photo, is_verified)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (desc, datetime.now().strftime("%Y-%m-%d"), loc, lat, lon, user_id, espece_id, filename, 1)
                )
                print(f"✅ Post ajouté pour : {nom_esp}")
            except Exception as e:
                print(f"🔥 Erreur insertion {nom_esp} : {e}")

        db.commit()
        print("\n✨ Base de données mise à jour avec succès !")

if __name__ == "__main__":
    seed_file_post()
