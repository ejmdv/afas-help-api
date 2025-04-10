from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from googlesearch import search
import requests
import openai
import os

app = FastAPI()

# API-key ophalen uit omgeving
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY niet gevonden in omgeving.")

class VraagInput(BaseModel):
    vraag: str

@app.post("/afas-help")
def afas_help(vraag_input: VraagInput):
    vraag = vraag_input.vraag

    try:
        print(f"[INFO] Vraag ontvangen: {vraag}")

        # Stap 1: Zoek de juiste AFAS-pagina via Google
        zoekterm = f"{vraag} site:help.afas.nl"
        print(f"[INFO] Zoekterm gegenereerd: {zoekterm}")

        resultaten = list(search(zoekterm, num_results=1))
        if not resultaten:
            print("[WARN] Geen zoekresultaten gevonden.")
            raise HTTPException(status_code=404, detail="Geen pagina gevonden op help.afas.nl")

        url = resultaten[0]
        print(f"[INFO] Eerste zoekresultaat: {url}")

        # Stap 2: Scrape de inhoud van de pagina
        pagina = requests.get(url, timeout=10)
        if pagina.status_code != 200:
            print(f"[ERROR] Pagina niet bereikbaar, statuscode: {pagina.status_code}")
            raise HTTPException(status_code=502, detail="AFAS-pagina niet bereikbaar")

        soup = BeautifulSoup(pagina.text, 'html.parser')
        tekst = soup.get_text(separator=' ', strip=True)[:8000]

        if not tekst.strip():
            print("[WARN] Geen tekst gevonden op de pagina.")
            raise HTTPException(status_code=500, detail="Pagina bevat geen bruikbare tekst")

        print(f"[INFO] Eerste 300 tekens AFAS Help:\n{tekst[:300]}")

        # Stap 3: Vraag naar OpenAI sturen
        prompt = f"""
Je bent een AFAS-expert. Gebruik onderstaande AFAS Help-tekst om de gebruikersvraag te beantwoorden:

AFAS Help:
\"\"\"
{tekst}
\"\"\"

Vraag:
{vraag}
"""

        print("[INFO] Stuur prompt naar OpenAI...")
        antwoord = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame AFAS-expert."},
                {"role": "user", "content": prompt}
            ]
        )

        resultaat = antwoord['choices'][0]['message']['content']
        print(f"[INFO] OpenAI antwoord gegenereerd (eerste 300 tekens): {resultaat[:300]}")
        return {"antwoord": resultaat}

    except Exception as e
