"""
EXPERIMENT: Solució B v2 — LLM parser + flux determinista (prompt millorat)
----------------------------------------------------------------------------
Prompt que indueix la inferència de camps implícits (lloc des del domini,
tipus_esdeveniment des del context, etc.).
CLI: python experiment.py --model qwen2.5:7b --backend local
     python experiment.py --model gemini-2.0-flash --backend cloud
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data.config import CAMPS_TOTS
from data.emails import CORREUS
from data.ground_truth import ACCIO_ESPERADA, CAMPS_DISPONIBLES_PER_EMAIL
from src.utils import (
    calcular_metriques,
    comptar_camps_extrets,
    executar_flux,
    guardar_resultat,
    sanititzar_dades,
)

GEMINI_MODEL    = "gemini-2.0-flash"
CLAUS_CORRECTES = set(CAMPS_TOTS)


def _build_prompt(correu: dict) -> str:
    return f"""Analitza el següent correu electrònic i extreu la informació en format JSON.
Si un camp no apareix al correu, posa null.
Les dates han d'estar en format YYYY-MM-DD si és possible, o null si és ambigua/desconeguda.
Infereix el camp si apareix de manera implícita: p.ex. el lloc des del nom de l'entitat
o del domini del correu, o el tipus_esdeveniment des del context.

Camps a extreure (retorna exactament aquestes claus):
- dia: data concreta de l'event (YYYY-MM-DD o null)
- lloc: ciutat o espai de l'event (string o null)
- tipus_esdeveniment: tipus d'event descrit lliurement (string o null)
- usuari: nom de l'entitat o persona que escriu (string o null)
- durada: durada estimada si s'esmenta (string o null)
- aforament: capacitat de l'espai si s'esmenta (integer o null)
- pressupost: pressupost mencionat (string o null)
- llengua: llengua principal del correu (ca/es/fr/en)

Respon ÚNICAMENT amb el JSON, sense cap text addicional.

Correu:
De: {correu['de']}
Assumpte: {correu['assumpte']}
Cos:
{correu['cos']}
"""


def _extraure_ollama(correu: dict, model: str) -> tuple[dict, bool]:
    import ollama
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": _build_prompt(correu)}],
        format="json",
    )
    try:
        raw = json.loads(resp.message.content)
        return sanititzar_dades(raw), CLAUS_CORRECTES.issubset(set(raw.keys()))
    except json.JSONDecodeError:
        return {}, False


def _extraure_gemini(correu: dict, api_key: str) -> tuple[dict, bool]:
    import time
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config={"response_mime_type": "application/json"},
    )
    for attempt in range(4):
        try:
            resp = model.generate_content(_build_prompt(correu))
            raw = json.loads(resp.text)
            return sanititzar_dades(raw), CLAUS_CORRECTES.issubset(set(raw.keys()))
        except json.JSONDecodeError:
            return {}, False
        except Exception as e:
            if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                wait = 65 * (attempt + 1)
                print(f"\n  [Quota Gemini] Esperant {wait}s (intent {attempt+1}/3)...")
                time.sleep(wait)
            else:
                raise
    return {}, False


def _processar_correu(correu: dict, model: str, backend: str, gemini_key: str) -> dict:
    print(f"\n{'='*60}\nCORREU #{correu['id']} — {correu['assumpte']}\n{'='*60}")
    print("\n[1] Extraient dades (prompt millorat)...")

    if backend == "local":
        dades, json_valid = _extraure_ollama(correu, model)
    else:
        dades, json_valid = _extraure_gemini(correu, gemini_key)

    print(json.dumps(dades, ensure_ascii=False, indent=2))
    accio = executar_flux(dades)
    print(f"\n>>> ACCIÓ: {accio}")

    accio_esp = ACCIO_ESPERADA[correu["id"]]
    return {
        "id": correu["id"],
        "assumpte": correu["assumpte"],
        "dades_extretes": dades,
        "json_valid": json_valid,
        "camps_extrets": comptar_camps_extrets(dades),
        "camps_disponibles": CAMPS_DISPONIBLES_PER_EMAIL[correu["id"]],
        "accio": accio,
        "accio_esperada": accio_esp,
        "accio_correcta": accio == accio_esp,
    }


def run(model: str, backend: str = "local") -> dict:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    if backend == "cloud" and (not gemini_key or gemini_key == "your_api_key_here"):
        raise ValueError("GEMINI_API_KEY no configurada al .env")

    print(f"\nSolució B v2 | Backend: {backend} | Model: {model}")
    resultats = [_processar_correu(c, model, backend, gemini_key) for c in CORREUS]
    metriques = calcular_metriques(resultats)
    model_label = model.replace(":", "_").replace(".", "_")
    return {
        "experiment_id": f"solucio_b_v2_{model_label}",
        "solucio": "B_v2",
        "model": model,
        "backend": backend,
        "data": str(date.today()),
        "emails": resultats,
        "metriques": metriques,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",   default="qwen2.5:7b")
    p.add_argument("--backend", default="local", choices=["local", "cloud"])
    args = p.parse_args()
    result = run(args.model, args.backend)
    model_label = args.model.replace(":", "_").replace(".", "_")
    guardar_resultat(result, ROOT / "model_statistics" / f"solucio_b_v2_{model_label}.json")
    m = result["metriques"]
    print(f"Accuracy: {m['accuracy']:.0%} | Score: {m['score']:.3f}")
