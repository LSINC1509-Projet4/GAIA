import math

def calculate_tot(nbre_posts, nbre_likes):
    """
    Calcule le total d'XP.
    Un post rapporte beaucoup (ex: 50 XP), un like un peu moins (ex: 10 XP).
    """
    return (nbre_posts * 50) + (nbre_likes * 10)

def calcul_levels(xp):
    """
    Calcule le niveau basé sur l'XP.
    Formule : Niveau = racine_carree(XP / 10)
    Avec cette formule :
    - Niveau 1 : 10 XP (0 post, 1 like)
    - Niveau 10 : 1000 XP (10 posts, 50 likes)
    - Niveau 20 : 4000 XP
    """
    if xp <= 0:
        return 1

    #  Niveau = sqrt(XP / factor)
    level = math.floor(math.sqrt(xp / 10))

    return max(1, level)
def badge(level):
    """
    Associe le titre et le Badge (avec emoji) selon le niveau.
    """
    if level is None:
        level = 1
    if level < 5:
        return "🌰 Graine de GAIA"
    if level < 10:
        return "🌱 Petit Germe"
    if level < 20:
        return "🌿 Germe développé"
    if level < 30:
        return "🪴 Jeune Pousse-un"
    if level < 40:
        return "🪵 Branche"
    if level < 50:
        return "🌿 Bourgeon"
    if level < 60:
        return "🍃 Feuille-osophe"
    if level < 70:
        return "🌸 Fleur"
    if level < 80:
        return "🌳 Tronc"
    if level < 90:
        return "✨ Arbre-acadabra"
    if level < 95:
        return "🍎 Petit Verger"

    # Lvl 95 et au-delà
    return "🌲 Forêt-midable"
