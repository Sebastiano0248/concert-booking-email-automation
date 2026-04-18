"""
API de Disponibilitat — Emulació amb dades de data/agenda.py
=============================================================
Consulta la disponibilitat de dates de l'agenda de l'associació.
En producció es substituiria per crides a una base de dades o API REST.
"""

from datetime import datetime

from data.agenda import DATES_OCUPADES


def _normalitzar_data(data: str | None) -> str | None:
    if data is None:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(data, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def consultar_disponibilitat_data(data: str) -> dict:
    """
    Comprova si una data té una actuació o reserva ja programada.

    Returns:
        {
            "data": str,
            "disponible": bool,
            "motiu": str
        }
    """
    data_norm = _normalitzar_data(data)
    if data_norm is None:
        return {"data": data, "disponible": False, "motiu": "Format de data no reconegut"}

    conflicte = DATES_OCUPADES.get(data_norm)
    return {
        "data": data_norm,
        "disponible": conflicte is None,
        "motiu": conflicte if conflicte else "Data lliure",
    }