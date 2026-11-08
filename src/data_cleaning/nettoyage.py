"""Nettoyage du dataset brut d'entreprises IT Marrakech."""

import os
import re
import sys
import pandas as pd
from difflib import SequenceMatcher

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.classification import detecter_quartier

COLONNES_ATTENDUES = [
    "ID", "Nom_Entreprise", "Domaine", "Sous_Domaine", "Adresse", "Quartier",
    "Telephone", "Email", "Site_Web", "Source", "Date_Collecte",
    "Rating", "Rating_Mediane", "Nb_Avis", "Note_Estimee", "Fiabilite_Quartier",
]

SEUIL_SIMILARITE_DOUBLONS = 0.85  # 90% de similarité = considéré comme doublon


def charger_donnees_brutes(chemin: str) -> pd.DataFrame:
    df = pd.read_excel(chemin)
    return df[COLONNES_ATTENDUES].copy()


def nettoyer_texte(valeur) -> str:
    """Supprime espaces superflus, normalise les espaces multiples."""
    if pd.isna(valeur):
        return "Non renseigné"
    texte = str(valeur).strip()
    texte = re.sub(r"\s+", " ", texte)
    return texte if texte else "Non renseigné"


def nettoyer_telephone(valeur) -> str:
    """Uniformise le format : 06 XX XX XX XX ou Non renseigné."""
    if pd.isna(valeur) or str(valeur).strip() in ("", "Non renseigné"):
        return "Non renseigné"
    chiffres = re.sub(r"\D", "", str(valeur))
    if chiffres.startswith("212"):
        chiffres = "0" + chiffres[3:]
    elif chiffres.startswith("00212"):
        chiffres = "0" + chiffres[5:]
    if len(chiffres) != 10 or not chiffres.startswith("0"):
        return "Non renseigné"  # format invalide, on ne garde pas une donnée fausse
    return " ".join([chiffres[i:i + 2] for i in range(0, 10, 2)])


def nettoyer_site_web(valeur) -> str:
    if pd.isna(valeur) or str(valeur).strip() in ("", "Non renseigné"):
        return "Non renseigné"
    url = str(valeur).strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def sont_similaires(nom1: str, nom2: str) -> bool:
    ratio = SequenceMatcher(None, nom1.lower(), nom2.lower()).ratio()
    return ratio >= SEUIL_SIMILARITE_DOUBLONS


def supprimer_doublons_flous(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Retire les lignes dont le nom est très proche d'une ligne déjà gardée."""
    indices_a_garder = []
    noms_gardes = []

    for idx, row in df.iterrows():
        nom = row["Nom_Entreprise"]
        est_doublon = any(sont_similaires(nom, nom_garde) for nom_garde in noms_gardes)
        if not est_doublon:
            indices_a_garder.append(idx)
            noms_gardes.append(nom)

    nb_supprimes = len(df) - len(indices_a_garder)
    return df.loc[indices_a_garder].copy(), nb_supprimes

def filtrer_contact_minimal(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Retire les entreprises sans aucun moyen de contact exploitable
    (ni téléphone valide, ni site web) : inutilisables pour candidater."""
    a_telephone = df["Telephone"] != "Non renseigné"
    a_site_web = df["Site_Web"] != "Non renseigné"
    masque_contact = a_telephone | a_site_web

    nb_supprimes = (~masque_contact).sum()
    return df[masque_contact].copy(), nb_supprimes

def nettoyer_donnees(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rapport = {
        "lignes_avant": len(df),
        "telephones_corriges": 0,
        "telephones_invalides": 0,
        "sites_web_corriges": 0,
        "quartiers_ameliores": 0,
        "doublons_flous_supprimes": 0,
        "ratings_estimes": 0,
    }

    df = df.copy()

    # Colonnes texte : nettoyage des espaces
    for col in ["Nom_Entreprise", "Domaine", "Sous_Domaine", "Adresse", "Source"]:
        df[col] = df[col].apply(nettoyer_texte)

    # Téléphone
    telephones_avant = df["Telephone"].copy()
    df["Telephone"] = df["Telephone"].apply(nettoyer_telephone)
    rapport["telephones_corriges"] = (telephones_avant.astype(str).str.strip() != df["Telephone"]).sum()
    rapport["telephones_invalides"] = (df["Telephone"] == "Non renseigné").sum()

    # Site web
    sites_avant = df["Site_Web"].copy()
    df["Site_Web"] = df["Site_Web"].apply(nettoyer_site_web)
    rapport["sites_web_corriges"] = (sites_avant.astype(str).str.strip() != df["Site_Web"]).sum()

    # Email : garder tel quel (toujours "Non renseigné" pour Google Places)
    df["Email"] = df["Email"].apply(nettoyer_texte)

    # Quartier : re-détection à partir de l'adresse nettoyée
    quartiers_avant = df["Quartier"].copy()
    resultats = df["Adresse"].apply(detecter_quartier)
    df["Quartier"] = resultats.apply(lambda x: x[0])
    df["Fiabilite_Quartier"] = resultats.apply(lambda x: x[1])
    rapport["quartiers_ameliores"] = (
        (quartiers_avant == "A_CONFIRMER") & (df["Quartier"] != "A_CONFIRMER")
    ).sum()

    # Types numériques
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(4.5)
    df["Rating_Mediane"] = pd.to_numeric(df["Rating_Mediane"], errors="coerce").fillna(df["Rating"])
    df["Nb_Avis"] = pd.to_numeric(df["Nb_Avis"], errors="coerce").fillna(0).astype(int)
    rapport["ratings_estimes"] = (df["Note_Estimee"] == "Oui").sum()

        # Doublons flous
    df, nb_doublons = supprimer_doublons_flous(df)
    rapport["doublons_flous_supprimes"] = nb_doublons

    # Filtre qualité : au moins un moyen de contact exploitable
    df, nb_sans_contact = filtrer_contact_minimal(df)
    rapport["supprimees_sans_contact"] = nb_sans_contact

    # Réattribution des ID après filtres
    df = df.reset_index(drop=True)
    df["ID"] = range(1, len(df) + 1)

    df = df[COLONNES_ATTENDUES]  # ordre garanti
    rapport["lignes_apres"] = len(df)

    return df, rapport


def sauvegarder_donnees_nettoyees(df: pd.DataFrame) -> str:
    """Sauvegarde le DataFrame nettoyé dans data/cleaned/data_nettoyee.xlsx."""
    dossier_racine = os.path.join(os.path.dirname(__file__), "..", "..")
    dossier_cleaned = os.path.join(dossier_racine, "data", "cleaned")
    os.makedirs(dossier_cleaned, exist_ok=True)

    chemin_fichier = os.path.join(dossier_cleaned, "data_nettoyee.xlsx")
    df.to_excel(chemin_fichier, index=False)
    return os.path.abspath(chemin_fichier)


def generer_rapport_qualite(rapport: dict) -> str:
    """Génère un rapport qualité lisible en xlsx dans data/reports/."""
    dossier_racine = os.path.join(os.path.dirname(__file__), "..", "..")
    dossier_reports = os.path.join(dossier_racine, "data", "reports")
    os.makedirs(dossier_reports, exist_ok=True)

    libelles = {
        "lignes_avant": "Nombre de lignes avant nettoyage",
        "telephones_corriges": "Numéros de téléphone corrigés (format)",
        "telephones_invalides": "Numéros de téléphone invalides (mis à 'Non renseigné')",
        "sites_web_corriges": "Sites web corrigés (ajout https://)",
        "quartiers_ameliores": "Quartiers précisés (A_CONFIRMER → détecté)",
        "doublons_flous_supprimes": "Doublons flous supprimés (entreprises identiques, noms variés)",
        "ratings_estimes": "Notes (Rating) estimées par défaut, faute de donnée Google",
        "supprimees_sans_contact": "Entreprises supprimées (aucun contact exploitable)",
        "lignes_apres": "Nombre de lignes après nettoyage",
    }

    lignes_rapport = []
    for cle, valeur in rapport.items():
        lignes_rapport.append({
            "Indicateur": libelles.get(cle, cle),
            "Valeur": valeur,
        })

    df_rapport = pd.DataFrame(lignes_rapport)
    chemin_fichier = os.path.join(dossier_reports, "rapport_qualite.xlsx")
    df_rapport.to_excel(chemin_fichier, index=False)
    return os.path.abspath(chemin_fichier)


if __name__ == "__main__":
    dossier_racine = os.path.join(os.path.dirname(__file__), "..", "..")
    chemin_brut = os.path.join(dossier_racine, "data", "raw", "data_brute.xlsx")

    df_brut = charger_donnees_brutes(chemin_brut)
    print(f"Données brutes chargées : {len(df_brut)} lignes")

    df_propre, rapport = nettoyer_donnees(df_brut)

    print("\n--- Rapport de nettoyage ---")
    for cle, valeur in rapport.items():
        print(f"{cle} : {valeur}")

    print(f"\nDonnées nettoyées : {len(df_propre)} lignes")

    chemin_data = sauvegarder_donnees_nettoyees(df_propre)
    print(f"\nDonnées nettoyées sauvegardées : {chemin_data}")

    chemin_rapport = generer_rapport_qualite(rapport)
    print(f"Rapport qualité sauvegardé : {chemin_rapport}")
    print(df_propre.head())