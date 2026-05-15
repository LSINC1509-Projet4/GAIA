"""
Télécharge plusieurs vraies photos d'observation depuis iNaturalist pour chaque
espèce. Lance UNE FOIS avant la démo (besoin d'internet, ~2-3 min).

Pourquoi iNaturalist plutôt que Wikipedia :
  - vraies photos d'observations (pas de planche taxonomique)
  - plusieurs photos par espèce (le seed pioche au hasard pour varier le feed)
  - photos correspondent vraiment à l'espèce

Les photos sont sauvegardées dans app/static/uploads/species/<safe_name>_<i>.jpg.
"""
import json
import os
import re
import sys
import time
from urllib import parse, request

# Console Windows : force UTF-8 (sinon les ✔/✗ et accents crashent en cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = os.path.join("app", "static", "uploads", "species")
USER_AGENT = "GAIA-LSINC1509/1.0 (school project; contact: gaia@uclouvain.be)"
PHOTOS_PER_SPECIES = 6      # combien de photos différentes on télécharge par espèce
API_DELAY = 0.5             # délai entre appels iNat (politesse)

# 26 espèces à présenter (toutes confirmées dans Animaux.csv)
ESPECES = [
    "Renard roux", "Renard polaire", "Renard gris", "Fennec",
    "Loup gris", "Loup arctique", "Loup du Mexique",
    "Hermine", "Hyène brune",
    "Porc domestique", "Vache Highland",
    "Maki catta", "Galéopithèque de la Sonde", "Rhinopithèque de Roxellane",
    "Chlamydophore tronqué", "Tangue zébré", "Quokka",
    "Mara de Patagonie",
    "Éléphant d'Asie", "Éléphant de Sumatra", "Éléphant de Bornéo",
    "Oryx d'Arabie", "Urial", "Antilope cervicapre",
    "Écureuil roux américain", "Écureuil de Douglas",
]


def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()


def http_get_json(url):
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def download(url, path):
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
        f.write(r.read())


def find_taxon_id(name):
    """Cherche un taxon iNaturalist par nom (FR), renvoie son id ou None."""
    url = (
        f"https://api.inaturalist.org/v1/taxa"
        f"?q={parse.quote(name)}&locale=fr&per_page=1"
    )
    data = http_get_json(url)
    results = data.get("results", [])
    return results[0]["id"] if results else None


def fetch_observation_photo_urls(taxon_id, n):
    """Renvoie jusqu'à n URLs de photos d'observations pour ce taxon.
    On filtre research-grade pour avoir des photos validées."""
    url = (
        f"https://api.inaturalist.org/v1/observations"
        f"?taxon_id={taxon_id}&photos=true&per_page={n * 2}"
        f"&order=desc&order_by=votes&quality_grade=research"
    )
    data = http_get_json(url)
    urls = []
    for obs in data.get("results", []):
        for p in obs.get("photos", []):
            u = p.get("url", "")
            # L'URL par défaut renvoie une vignette 75x75 ; on prend la version medium (~500px)
            urls.append(u.replace("/square.", "/medium."))
            if len(urls) >= n:
                return urls
    return urls


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Téléchargement depuis iNaturalist : {len(ESPECES)} espèces × {PHOTOS_PER_SPECIES} photos max")
    print(f"Destination : {OUT_DIR}\n")

    total_dl = 0
    sans_taxon = []
    sans_photo = []

    for nom in ESPECES:
        safe = safe_filename(nom)
        try:
            taxon_id = find_taxon_id(nom)
            if not taxon_id:
                print(f"  ✗ {nom} : taxon introuvable")
                sans_taxon.append(nom)
                continue
            time.sleep(API_DELAY)

            urls = fetch_observation_photo_urls(taxon_id, PHOTOS_PER_SPECIES)
            if not urls:
                print(f"  ✗ {nom} : aucune observation avec photo")
                sans_photo.append(nom)
                continue

            n_dl = 0
            for i, u in enumerate(urls):
                out = os.path.join(OUT_DIR, f"{safe}_{i + 1}.jpg")
                if os.path.exists(out):
                    n_dl += 1
                    continue
                try:
                    download(u, out)
                    n_dl += 1
                    time.sleep(0.2)
                except Exception:
                    pass  # un échec sur une photo ne bloque pas les autres
            print(f"  ✔ {nom} → {n_dl} photo(s)")
            total_dl += n_dl
            time.sleep(API_DELAY)
        except Exception as e:
            print(f"  ✗ {nom} : {e}")
            sans_photo.append(nom)

    print(f"\n{total_dl} photos téléchargées pour {len(ESPECES) - len(sans_taxon) - len(sans_photo)} espèces.")
    if sans_taxon:
        print(f"Taxon introuvable ({len(sans_taxon)}) : {sans_taxon}")
    if sans_photo:
        print(f"Sans photo ({len(sans_photo)}) : {sans_photo}")
    print("\n🚀 Tu peux maintenant lancer 'python -m tests.seed_demo'")


if __name__ == "__main__":
    main()
