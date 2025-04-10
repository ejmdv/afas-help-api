from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
from googlesearch import search
import requests

app = FastAPI()

class VraagInput(BaseModel):
    vraag: str

@app.post("/afas-tekst")
def afas_tekst(vraag_input: VraagInput):
    vraag = vraag_input.vraag

    try:
        print(f"[INFO] Vraag ontvangen: {vraag}")

        # Google zoekopdracht: alleen binnen help.afas.nl
        zoekterm = f"{vraag} site:help.afas.nl"
        resultaten = list(search(zoekterm, num_results=1))

        if not resultaten:
            print("[WAARSCHUWING] Geen zoekresultaten gevonden.")
            raise HTTPException(status_code=404, detail="Geen AFAS Help-pagina gevonden.")

        url = resultaten[0]
        print(f"[INFO] Eerste zoekresultaat: {url}")

        # Headers om toegang te krijgen tot de pagina
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        pagina = requests.get(url, headers=headers, timeout=10)
        if pagina.status_code != 200:
            print(f"[FOUT] Statuscode ontvangen: {pagina.status_code}")
            raise HTTPException(status_code=502, detail="AFAS-pagina niet bereikbaar")

        # Tekst extraheren
        soup = BeautifulSoup(pagina.text, 'html.parser')
        tekst = soup.get_text(separator=' ', strip=True)

        if not tekst.strip():
            raise HTTPException(status_code=500, detail="De pagina bevat geen bruikbare tekst")

        print(f"[INFO] Tekst succesvol opgehaald ({len(tekst)} tekens)")

        return {
            "url": url,
            "afas_tekst": tekst[:8000]  # Eventuele limiet voor lang output
        }

    except Exception as e:
        print(f"[FOUT] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
