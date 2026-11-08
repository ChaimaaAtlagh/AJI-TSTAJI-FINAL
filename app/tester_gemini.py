"""
tester_gemini.py
Vérifie la connexion à Gemini avec la clé du fichier .env :
  1. la clé est-elle trouvée ? (elle n'est JAMAIS affichée)
  2. quels modèles de texte sont réellement disponibles avec cette clé ?
  3. le modèle choisi répond-il ?

Lancement (depuis la racine du projet) :
    python tester_gemini.py
"""
import os
import sys
from dotenv import load_dotenv

RACINE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(RACINE, ".env"))
sys.path.insert(0, RACINE)

from app.chatbot_page import ChatbotPage, MODELE_PAR_DEFAUT

try:
    from google import genai
except ImportError:
    print("Bibliothèque manquante. Installe-la avec : pip install -U google-genai")
    sys.exit(1)

cle = os.getenv("GEMINI_API_KEY", "").strip()
if not cle:
    print("GEMINI_API_KEY est vide ou absente du fichier .env.")
    sys.exit(1)
print("Clé GEMINI_API_KEY trouvée (non affichée).")


def masquer(texte):
    return str(texte).replace(cle, "***")


client = genai.Client(api_key=cle)

try:
    noms = sorted(ChatbotPage._modeles_disponibles(client))
except Exception as erreur:
    print("Impossible de lister les modèles :", masquer(erreur)[:400])
    sys.exit(1)

print("\nModèles disponibles avec cette clé (generateContent) :")
for nom in noms:
    print("  -", nom)

modele = os.getenv("GEMINI_MODEL", "").strip() or MODELE_PAR_DEFAUT
if modele not in noms:
    print("\nLe modèle « %s » n'est PAS dans la liste." % modele)
    modele = ChatbotPage._meilleur_modele_texte(noms)
    if not modele:
        print("Aucun modèle Flash de texte trouvé. Choisis-en un dans la liste ci-dessus.")
        sys.exit(1)
    print("Modèle proposé :", modele)
    print("Pour le fixer, ajoute dans .env :  GEMINI_MODEL=" + modele)

print("\nTest d'un message avec le modèle :", modele)
try:
    reponse = client.models.generate_content(model=modele, contents="Réponds juste : OK")
    print("Réponse :", (getattr(reponse, "text", "") or "").strip()[:200])
    print("\nTout fonctionne.")
except Exception as erreur:
    print("Échec :", masquer(erreur)[:400])
    sys.exit(1)