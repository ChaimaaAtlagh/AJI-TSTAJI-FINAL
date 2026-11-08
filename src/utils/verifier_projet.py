"""
verifier_projet.py
Vérification EN LECTURE SEULE du projet Aji Tstaji.
Ce script ne crée, ne modifie et ne supprime aucun fichier.

Utilisation :
    python src/utils/verifier_projet.py
"""

from pathlib import Path

# Racine du projet : on remonte de 2 niveaux (src/utils/ -> racine)
RACINE = Path(__file__).resolve().parents[2]

# Fichiers qui doivent exister (ta partie DATA, à conserver telle quelle)
FICHIERS_A_CONSERVER = [
    "data/raw/data_brute.xlsx",
    "data/cleaned/data_nettoyee.xlsx",
    "data/reports/rapport_qualite.xlsx",
    "src/data_collection/google_places.py",
    "src/data_cleaning/nettoyage.py",
    ".env",
]

# Restes de l'ancien projet : on les signale seulement, on ne les touche pas
RESTES_ANCIEN_PROJET = [
    "node_modules",
    "app/frontend",
    "package.json",
    "data/reports/graphiques",
]


def taille_lisible(chemin):
    """Retourne la taille d'un fichier en Ko."""
    return f"{chemin.stat().st_size / 1024:.1f} Ko"


def verifier_fichiers():
    """Vérifie que les fichiers à conserver sont présents."""
    print("=== FICHIERS À CONSERVER ===")
    manquants = 0
    for chemin in FICHIERS_A_CONSERVER:
        fichier = RACINE / chemin
        if fichier.is_file():
            print(f"[OK]       {chemin}  ({taille_lisible(fichier)})")
        else:
            print(f"[MANQUANT] {chemin}")
            manquants += 1
    return manquants


def signaler_anciens_restes():
    """Signale les restes de l'ancien projet (information seulement)."""
    print("\n=== RESTES DE L'ANCIEN PROJET (information, rien n'est touché) ===")
    trouve = False
    for chemin in RESTES_ANCIEN_PROJET:
        if (RACINE / chemin).exists():
            print(f"[PRÉSENT]  {chemin}")
            trouve = True
    if not trouve:
        print("Aucun reste détecté.")


def lister_dossiers():
    """Liste les dossiers à la racine et le contenu de app/ et src/ (sans node_modules)."""
    print("\n=== DOSSIERS À LA RACINE ===")
    for element in sorted(RACINE.iterdir()):
        if element.is_dir() and element.name not in {".git", ".venv", "venv", "node_modules"}:
            print(f"  {element.name}/")

    for nom in ["app", "src"]:
        dossier = RACINE / nom
        print(f"\n=== FICHIERS DANS {nom}/ ===")
        if not dossier.is_dir():
            print("  (dossier absent)")
            continue
        for fichier in sorted(dossier.rglob("*")):
            parties = fichier.relative_to(RACINE).parts
            if fichier.is_file() and "node_modules" not in parties and "__pycache__" not in parties:
                print(f"  {fichier.relative_to(RACINE)}")


if __name__ == "__main__":
    print(f"Racine du projet : {RACINE}\n")
    nb_manquants = verifier_fichiers()
    signaler_anciens_restes()
    lister_dossiers()
    print("\n=== BILAN ===")
    if nb_manquants == 0:
        print("Tous les fichiers à conserver sont présents.")
    else:
        print(f"{nb_manquants} fichier(s) manquant(s) : ne supprime rien, dis-le-moi.")