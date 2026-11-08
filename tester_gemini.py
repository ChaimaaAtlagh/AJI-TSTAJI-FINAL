import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
cle = os.getenv("GEMINI_API_KEY", "").strip()
print("Clé trouvée (non affichée)." if cle else "Clé absente du fichier .env.")
client = genai.Client(api_key=cle)
try:
    r = client.models.generate_content(model="gemini-3.8-flash", contents="Réponds juste : OK")
    print("Réponse :", r.text)
    print("Tout fonctionne.")
except Exception as e:
    print("Échec :", str(e).replace(cle, "***")[:400])
