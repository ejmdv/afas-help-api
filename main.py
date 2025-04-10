from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from googlesearch import search
import requests
import openai
import os

app = FastAPI()

# Vul hier je OpenAI API-key in of zet hem als omgeving variabele
openai.api_key = os.getenv("OPENAI_API_KEY")

class VraagInput(BaseModel):
    vraag: str

@app.post("/afas-help")
def afas_help(vraag_input: VraagInput):
    vraag = vraag_input.vraag

    try:
        zoekterm = f"{vraag} site:help.afas.nl"
        resultaten = list(search(zoekterm, num_results=1))

        if not resultaten:
            raise HTTPException(status_code=404, detail="Geen pagina gevonden")

        url = resultaten[0]
        pagina = requests.get(url, timeout=10)
        soup = BeautifulSoup(pagina.text, 'html.parser')
        tekst = soup.get_text(separator=' ', strip=True)[:8000]

        prompt = f"""
Je bent een AFAS-expert. Gebruik onderstaande AFAS Help-tekst om de gebruikersvraag te beantwoorden:

AFAS Help:
\"\"\"
{tekst}
\"\"\"

Vraag:
{vraag}
"""

        antwoord = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame AFAS-expert."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"antwoord": antwoord['choices'][0]['message']['content']}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
