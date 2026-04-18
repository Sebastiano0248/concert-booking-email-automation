"""
Utils — Codi comú per a tots els experiments
"""

import json
from pathlib import Path

from data.config import CAMPS_REQUERITS, CAMPS_TOTS
from data.ground_truth import ACCIO_ESPERADA, CAMPS_DISPONIBLES_PER_EMAIL
from src.api_disponibilitat import consultar_disponibilitat_data


def identificar_info_faltant(dades: dict) -> list[str]:
    return [camp for camp in CAMPS_REQUERITS if not dades.get(camp)]


def executar_flux(dades: dict) -> str:
    """
    Flux determinista:
      1. Si falta informació obligatòria → demanar_info
      2. Si la data és ocupada → denegar_data
      3. Si tot correcte → guardar
    """
    info_faltant = identificar_info_faltant(dades)
    if info_faltant:
        return "demanar_info"

    res_cal = consultar_disponibilitat_data(dades["dia"])
    if not res_cal["disponible"]:
        return "denegar_data"

    return "guardar"


def comptar_camps_extrets(dades: dict) -> int:
    return sum(1 for k in CAMPS_TOTS if dades.get(k) is not None)


def sanititzar_dades(raw: dict) -> dict:
    return {k: (None if v in ("null", "") else v) for k, v in raw.items()}


def calcular_metriques(resultats_emails: list[dict]) -> dict:
    n = len(resultats_emails)
    correctes       = sum(1 for r in resultats_emails if r["accio_correcta"])
    json_ok         = sum(1 for r in resultats_emails if r.get("json_valid", True))
    tool_ok         = sum(1 for r in resultats_emails if r.get("eines_cridades"))
    ratios          = [
        min(r["camps_extrets"] / r["camps_disponibles"], 1.0)
        for r in resultats_emails
        if r.get("camps_extrets") is not None and r.get("camps_disponibles")
    ]
    accuracy        = correctes / n
    json_valid_rate = json_ok / n
    avg_extraccio   = round(sum(ratios) / len(ratios), 3) if ratios else None
    tool_rate       = round(tool_ok / n, 3) if any(
        r.get("eines_cridades") is not None for r in resultats_emails
    ) else None

    if avg_extraccio is not None:
        score = accuracy * 0.5 + json_valid_rate * 0.2 + avg_extraccio * 0.3
    else:
        score = accuracy * 0.6 + json_valid_rate * 0.4

    return {
        "accuracy":               round(accuracy, 3),
        "tool_call_success_rate": tool_rate,
        "json_valid_rate":        round(json_valid_rate, 3),
        "avg_extraccio":          avg_extraccio,
        "score":                  round(score, 3),
    }


def guardar_resultat(resultat: dict, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)
    print(f"\nResultat guardat a: {output_path.name}")
