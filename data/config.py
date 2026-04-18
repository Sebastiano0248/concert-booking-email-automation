"""
Configuració del projecte: camps a extreure i camps obligatoris.
Tots els experiments llegeixen d'aquí per garantir consistència.
"""

# Camps que el LLM ha d'extreure de cada correu
CAMPS_TOTS: list[str] = [
    "dia",                  # Data concreta de l'event (YYYY-MM-DD)
    "lloc",                 # Ciutat o espai de l'event
    "tipus_esdeveniment",   # String lliure (concert, festival, privat, etc.)
    "usuari",               # Nom de l'entitat o persona que escriu
    "durada",               # Durada estimada (default 1.5h si no s'especifica)
    "aforament",            # Capacitat de l'espai (opcional)
    "pressupost",           # Pressupost mencionat pel sol·licitant (opcional)
    "llengua",              # Llengua principal del correu (ca/es/fr/en)
]

# Camps obligatoris per continuar el flux
CAMPS_REQUERITS: list[str] = ["dia", "lloc", "tipus_esdeveniment", "usuari"]

# Durada per defecte si el correu no l'especifica
DURADA_DEFAULT = "1.5h"
