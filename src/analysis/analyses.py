"""Analyses et graphiques sur le dataset nettoyé d'entreprises IT Marrakech."""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

DOSSIER_RACINE = os.path.join(os.path.dirname(__file__), "..", "..")
CHEMIN_DATA = os.path.join(DOSSIER_RACINE, "data", "cleaned", "data_nettoyee.xlsx")
DOSSIER_GRAPHIQUES = os.path.join(DOSSIER_RACINE, "data", "reports", "graphiques")


def charger_donnees() -> pd.DataFrame:
    return pd.read_excel(CHEMIN_DATA)


def graphique_repartition_domaine(df: pd.DataFrame):
    plt.figure(figsize=(8, 6))
    compte = df["Domaine"].value_counts()
    sns.barplot(x=compte.values, y=compte.index, hue=compte.index, palette="viridis", legend=False)
    plt.title("Répartition des entreprises par domaine")
    plt.xlabel("Nombre d'entreprises")
    plt.ylabel("Domaine")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "repartition_domaine.png"), dpi=150)
    plt.close()


def graphique_repartition_sous_domaine(df: pd.DataFrame):
    plt.figure(figsize=(8, 6))
    compte = df["Sous_Domaine"].value_counts().head(10)
    sns.barplot(x=compte.values, y=compte.index, hue=compte.index, palette="mako", legend=False)
    plt.title("Top 10 des sous-domaines")
    plt.xlabel("Nombre d'entreprises")
    plt.ylabel("Sous-domaine")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "repartition_sous_domaine.png"), dpi=150)
    plt.close()


def graphique_repartition_quartier(df: pd.DataFrame):
    plt.figure(figsize=(8, 6))
    compte = df["Quartier"].value_counts()
    sns.barplot(x=compte.values, y=compte.index, hue=compte.index, palette="crest", legend=False)
    plt.title("Répartition des entreprises par quartier")
    plt.xlabel("Nombre d'entreprises")
    plt.ylabel("Quartier")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "repartition_quartier.png"), dpi=150)
    plt.close()


def graphique_distribution_rating(df: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    sns.histplot(df["Rating"], bins=10, kde=True, color="steelblue")
    plt.title("Distribution des notes (Rating) des entreprises")
    plt.xlabel("Rating")
    plt.ylabel("Nombre d'entreprises")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "distribution_rating.png"), dpi=150)
    plt.close()


def graphique_top_avis(df: pd.DataFrame):
    plt.figure(figsize=(9, 6))
    top10 = df.nlargest(10, "Nb_Avis")[["Nom_Entreprise", "Nb_Avis"]]
    sns.barplot(x="Nb_Avis", y="Nom_Entreprise", data=top10, hue="Nom_Entreprise", palette="flare", legend=False)
    plt.title("Top 10 des entreprises par nombre d'avis Google")
    plt.xlabel("Nombre d'avis")
    plt.ylabel("Entreprise")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "top10_avis.png"), dpi=150)
    plt.close()


def graphique_rating_moyen_par_domaine(df: pd.DataFrame):
    plt.figure(figsize=(8, 6))
    moyenne = df.groupby("Domaine")["Rating"].mean().sort_values(ascending=False)
    sns.barplot(x=moyenne.values, y=moyenne.index, hue=moyenne.index, palette="rocket", legend=False)
    plt.title("Rating moyen par domaine")
    plt.xlabel("Rating moyen")
    plt.ylabel("Domaine")
    plt.xlim(0, 5)
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER_GRAPHIQUES, "rating_moyen_domaine.png"), dpi=150)
    plt.close()


def generer_toutes_les_analyses():
    os.makedirs(DOSSIER_GRAPHIQUES, exist_ok=True)
    df = charger_donnees()

    print(f"Données chargées : {len(df)} entreprises")

    graphique_repartition_domaine(df)
    graphique_repartition_sous_domaine(df)
    graphique_repartition_quartier(df)
    graphique_distribution_rating(df)
    graphique_top_avis(df)
    graphique_rating_moyen_par_domaine(df)

    print(f"\n6 graphiques générés dans : {os.path.abspath(DOSSIER_GRAPHIQUES)}")

    # Résumé statistique texte
    print("\n--- Résumé statistique ---")
    print(f"Nombre total d'entreprises : {len(df)}")
    print(f"Rating moyen global : {df['Rating'].mean():.2f}")
    print(f"Nombre d'avis moyen : {df['Nb_Avis'].mean():.1f}")
    print(f"Domaine le plus représenté : {df['Domaine'].value_counts().idxmax()}")
    print(f"Quartier le plus représenté : {df['Quartier'].value_counts().idxmax()}")


if __name__ == "__main__":
    generer_toutes_les_analyses()