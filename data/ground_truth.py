"""
Ground truth per als 20 correus de test.
Defineix l'acció esperada i els camps disponibles per email.
"""

# Acció correcta que hauria de prendre el flux per a cada correu
ACCIO_ESPERADA: dict[int, str] = {
    1:  "guardar",       # Tota la info present, 2026-08-15 lliure → guardar proposta
    2:  "demanar_info",  # Falta dia (no concret)
    3:  "guardar",       # Tota la info present, 2026-07-22 lliure → guardar proposta
    4:  "demanar_info",  # Falta dia (setmana Festa Major, sense data)
    5:  "denegar_data",  # Data 2026-10-03 ocupada (Sala Razzmatazz)
    6:  "guardar",       # Tota la info present, 2026-09-15 lliure → guardar proposta
    7:  "guardar",       # Tota la info present, 2026-06-21 lliure → guardar proposta
    8:  "guardar",       # Tota la info present, 2026-07-05 lliure → guardar proposta
    9:  "guardar",       # Tota la info present (+ durada), 2026-11-14 lliure → guardar proposta
    10: "demanar_info",  # Falta dia (estiu 2026, sense data concreta)
    11: "demanar_info",  # Falta lloc (restaurant pendent de confirmar)
    12: "demanar_info",  # Falta dia (juliol o agost, sense data concreta)
    13: "demanar_info",  # Falta tipus_esdeveniment (format per decidir)
    14: "denegar_data",  # Data 2026-08-22 ocupada (Festival Sants)
    15: "denegar_data",  # Data 2026-12-31 ocupada (Cap d'Any privat)
    16: "denegar_data",  # Data 2026-12-25 festiu (sense actuacions)
    17: "guardar",       # Tota la info present (+ durada), 2026-05-20 lliure → guardar proposta
    18: "demanar_info",  # Falta dia i lloc (en fase de planificació)
    19: "denegar_data",  # Data 2026-10-03 ocupada (Sala Razzmatazz)
    20: "demanar_info",  # Falta usuari (email anònim sense identificació)
}

# Nombre de camps amb valor real a cada correu (per calcular ratio d'extracció)
# Camps: dia, lloc, tipus_esdeveniment, usuari, durada, aforament, pressupost, llengua
CAMPS_DISPONIBLES_PER_EMAIL: dict[int, int] = {
    1:  7,   # Falta durada
    2:  5,   # Falta dia i durada
    3:  7,   # Falta durada
    4:  4,   # Falta dia, durada, aforament i pressupost
    5:  6,   # Falta durada i pressupost
    6:  7,   # Falta durada
    7:  7,   # Falta durada
    8:  7,   # Falta durada
    9:  8,   # Tots els camps presents (inclou durada)
    10: 6,   # Falta dia i durada
    11: 6,   # Falta lloc i durada
    12: 6,   # Falta dia i durada
    13: 5,   # Falta tipus_esdeveniment, durada i pressupost
    14: 7,   # Falta durada
    15: 7,   # Falta durada
    16: 7,   # Falta durada
    17: 8,   # Tots els camps presents (inclou durada)
    18: 5,   # Falta dia, lloc i durada
    19: 7,   # Falta durada
    20: 4,   # Falta usuari, durada, aforament i pressupost
}
