from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from googlesearch import search
import requests
import os
from openai import OpenAI

app = FastAPI()

# OpenAI client aanmaken
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class VraagInput(BaseModel):
    vraag: str

@app.post("/afas-help")
def afas_help(vraag_input: VraagInput):
    vraag = vraag_input.vraag

    try:
        print(f"[INFO] Vraag ontvangen: {vraag}")

        zoekterm = f"{vraag} site:help.afas.nl"
        print(f"[INFO] Zoekterm: {zoekterm}")
        resultaten = list(search(zoekterm, num_results=1))

        if not resultaten:
            print("[WARN] Geen zoekresultaten.")
            raise HTTPException(status_code=404, detail="Geen AFAS-pagina gevonden")

        url = resultaten[0]
        print(f"[INFO] Gekozen URL: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "nl,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive"
        }

        pagina = requests.get(url, headers=headers, timeout=10)
        if pagina.status_code != 200:
            print(f"[ERROR] Statuscode {pagina.status_code} ontvangen.")
            raise HTTPException(status_code=502, detail="AFAS-pagina niet bereikbaar")

        soup = BeautifulSoup(pagina.text, 'html.parser')
        tekst = soup.get_text(separator=' ', strip=True)[:8000]

        if not tekst.strip():
            print("[WARN] Geen tekst gevonden op pagina.")
            raise HTTPException(status_code=500, detail="Lege pagina")

        print(f"[INFO] Eerste 300 tekens van AFAS Help:\n{tekst[:300]}")

        prompt = f"""
Je bent een AFAS-expert. Gebruik onderstaande AFAS Help-tekst om de gebruikersvraag te beantwoorden:

AFAS Help:
\"\"\"
{tekst}
\"\"\"

Vraag:
{vraag}
"""

        print("[INFO] Verstuur prompt naar OpenAI...")
        antwoord = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame AFAS-expert."},
                {"role": "user", "content": prompt}
            ]
        )

        resultaat = antwoord.choices[0].message.content
        print(f"[INFO] Antwoord gegenereerd:\n{resultaat[:300]}")
        return {"antwoord": resultaat}

    except Exception as e:
        print(f"[FOUT] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
