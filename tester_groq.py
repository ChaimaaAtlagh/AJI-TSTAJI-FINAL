
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

RACINE = Path(__file__).resolve().parent
load_dotenv(RACINE / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Erreur : GROQ_API_KEY introuvable dans .env")
    raise SystemExit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es l'assistant IA de AJI TSTAJI, "
                    "une application dédiée aux stages et emplois "
                    "dans les domaines de l'IA et de la Data à Marrakech."
                )
            },
            {
                "role": "user",
                "content": "Bonjour, présente brièvement AJI TSTAJI."
            }
        ],
        max_completion_tokens=300
    )

    print("Réponse de Groq :")
    print(response.choices[0].message.content)

except Exception as e:
    print("Échec du test :", e)
