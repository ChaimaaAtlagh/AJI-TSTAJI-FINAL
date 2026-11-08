"""Collecte des entreprises IT à Marrakech via Google Places API (New)."""

import os
import sys
import time
import requests
import pandas as pd
from datetime import date
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.classification import classifier_domaine, detecter_quartier, est_pertinent_it

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

REQUETES = [
    "agence de développement web Marrakech",
    "société informatique Marrakech",
    "agence de développement mobile Marrakech",
    "cybersécurité Marrakech",
    "intelligence artificielle Marrakech",
    "infrastructure réseau informatique Marrakech",
    "hébergement cloud Marrakech",
    "agence digitale Marrakech",
    "startup tech Marrakech",
    "société IT Guéliz Marrakech",
    "développeur freelance Marrakech",
    "conseil informatique Marrakech",
    "création application Marrakech",
    "solutions ERP Marrakech",
    "agence web Sidi Ghanem Marrakech",
    "entreprise informatique Marrakech",
    "développement logiciel Marrakech",
    "agence de communication digitale Marrakech",
]

FIELD_MASK_SEARCH = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.nationalPhoneNumber,places.websiteUri,"
    "places.rating,places.userRatingCount,places.types"
)


def requete_avec_retry(methode, url, max_essais=5, **kwargs):
    """Exécute une requête HTTP avec retry en cas de 429 (backoff exponentiel)."""
    for essai in range(max_essais):
        response = methode(url, **kwargs)
        if response.status_code == 429:
            print("  Détail de l'erreur Google :", response.text)
            attente = 2 ** essai
            print(f"  429 reçu, pause de {attente}s avant nouvel essai...")
            time.sleep(attente)
            continue
        response.raise_for_status()
        return response
    raise RuntimeError("Trop de 429 consécutifs, arrêt.")


def rechercher_lieux(requete: str) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK_SEARCH,
    }
    body = {"textQuery": requete, "languageCode": "fr", "regionCode": "MA"}
    response = requete_avec_retry(requests.post, SEARCH_URL, json=body, headers=headers)
    return response.json().get("places", [])


def construire_ligne(lieu: dict, idx: int, requete_source: str) -> dict:
    nom = lieu.get("displayName", {}).get("text", "Inconnu")
    adresse = lieu.get("formattedAddress", "Non renseigné")
    types_str = " ".join(lieu.get("types", []))
    domaine, sous_domaine = classifier_domaine(f"{nom} {types_str}")
    quartier, fiabilite = detecter_quartier(adresse)

    rating = lieu.get("rating")
    nb_avis = lieu.get("userRatingCount", 0)
    note_estimee = "Non"
    if rating is None:
        rating = 4.5
        note_estimee = "Oui"

    return {
        "ID": idx,
        "Nom_Entreprise": nom,
        "Domaine": domaine,
        "Sous_Domaine": sous_domaine,
        "Adresse": adresse,
        "Quartier": quartier,
        "Telephone": lieu.get("nationalPhoneNumber", "Non renseigné"),
        "Email": "Non renseigné",
        "Site_Web": lieu.get("websiteUri", "Non renseigné"),
        "Source": "Google Maps (Places API)",
        "Date_Collecte": date.today().strftime("%d/%m/%Y"),
        "Rating": rating,
        "Rating_Mediane": rating,
        "Nb_Avis": nb_avis,
        "Note_Estimee": note_estimee,
        "Fiabilite_Quartier": fiabilite,
    }


def collecter_toutes_entreprises() -> pd.DataFrame:
    """Collecte brute : PAS de dédoublonnage ici, on garde les doublons
    entre requêtes tels quels — c'est le rôle du nettoyage (ÉTAPE 6) de les traiter."""
    if not API_KEY:
        raise ValueError("GOOGLE_PLACES_API_KEY manquante dans .env")

    lignes = []
    idx = 1

    for requete in REQUETES:
        print(f"Recherche : {requete}")
        lieux = rechercher_lieux(requete)
        for lieu in lieux:
            nom = lieu.get("displayName", {}).get("text", "")
            if not est_pertinent_it(nom):
                print(f"  Ignoré (non IT) : {nom}")
                continue

            lignes.append(construire_ligne(lieu, idx, requete))
            idx += 1

        time.sleep(1)  # pause entre chaque requête de recherche

    return pd.DataFrame(lignes)


def sauvegarder_donnees_brutes(df: pd.DataFrame) -> str:
    """Sauvegarde le DataFrame collecté dans data/raw/data_brute.xlsx."""
    dossier_racine = os.path.join(os.path.dirname(__file__), "..", "..")
    dossier_raw = os.path.join(dossier_racine, "data", "raw")
    os.makedirs(dossier_raw, exist_ok=True)

    chemin_fichier = os.path.join(dossier_raw, "data_brute.xlsx")
    df.to_excel(chemin_fichier, index=False)
    return os.path.abspath(chemin_fichier)


if __name__ == "__main__":
    df = collecter_toutes_entreprises()
    print(f"\n{len(df)} lignes brutes collectées (avec doublons entre requêtes).")
    print(df.head())

    chemin = sauvegarder_donnees_brutes(df)
    print(f"\nFichier sauvegardé : {chemin}")