# Automatització de la gestió de correus de contractació de concerts

> **Estat: en procés** — s'està treballant en l'addició de RAG i fine-tuning amb dades reals.

Prova de concepte de dues aproximacions per automatitzar la gestió de correus
d'entitats interessades en contractar un concert.

---

## El problema

Una associació rep correus d'entitats interessades en contractar-los per fer un concert.
Gestionar aquests correus és una tasca repetitiva que implica:

- Identificar la informació rellevant del correu (data, ubicació, tipus d'event...)
- Consultar si la ubicació és viable segons certs criteris
- Comprovar si aquell dia ja hi ha una altra quedada programada
- Respondre al client si falta informació necessària

El repte principal és que **els correus arriben en format completament lliure**: cada
client escriu de manera diferent, amb les dades en posicions i formats variats, en
qualsevol llengua, i sense cap estructura predefinida. Això fa impossible automatitzar
la tasca amb regles fixes.

---

## Solució A — Agent autònom (Flowise / LangChain)

Un agent LLM rep el correu i decideix de forma autònoma quins passos seguir:
consultar eines, demanar informació, enviar respostes...

**Avantatges:**
- Molt flexible, gestiona casos inesperats
- No cal definir el flux manualment

**Inconvenients:**
- Impredictible: el model pot prendre decisions incorrectes
- Difícil de depurar quan s'equivoca
- Cost elevat en tokens LLM
- Excés d'enginyeria per a un problema que no ho requereix

---

## Solució B — LLM com a parser dins d'un flux determinista (recomanada)

Es divideix el problema en dues capes:

### Capa 1 — Comprensió (LLM)
El model rep el correu i extreu les dades estructurades, per exemple:

```json
{
  "data": "2026-06-15",
  "ubicacio": "Girona",
  "tipus_event": "festa major",
  "informacio_faltant": ["aforament", "pressupost"]
}
```

El LLM **no pren decisions**: només entén el text lliure i el transforma en dades.

### Capa 2 — Decisió (flux determinista)
A partir de les dades estructurades, un flux fix (amb eines com n8n o Make.com)
executa les accions corresponents:

- Si hi ha `ubicacio` → consultar viabilitat
- Si hi ha `data` → comprovar el calendari
- Si hi ha `informacio_faltant` → enviar resposta automàtica al client

**Avantatges:**
- Robust i auditable: cada decisió és traçable
- Barat: el LLM només s'usa per a l'extracció
- Fàcil de modificar: canviar una regla no afecta la resta
- Suficient per cobrir el cas d'ús real

**Inconvenients:**
- Menys flexible davant casos molt atípics
- Requereix definir bé les regles del flux inicialment

---

## Especificació dels correus

### Idiomes suportats
- Català, Castellà, Francès

### Dades a extreure
| Camp | Obligatori | Notes |
|---|---|---|
| `dia` | Sí | Data concreta de l'event (YYYY-MM-DD) |
| `lloc` | Sí | Ciutat o espai de l'event |
| `tipus_esdeveniment` | Sí | String lliure — cal inferir si és públic o privat (afecta el preu) |
| `usuari` | Sí | Nom de l'entitat o persona que escriu |
| `durada` | No | Default: 1,5h |
| `aforament` | No | Capacitat de l'espai |
| `pressupost` | No | Pressupost mencionat pel sol·licitant |

### Flux esperat
1. Extreure les dades del correu.
2. Si falta informació obligatòria (`dia`, `lloc`, `tipus_esdeveniment`, `usuari`), demanar-la per correu.
3. Comprovar disponibilitat de la data a l'agenda.
4. Si la data és ocupada, notificar al sol·licitant.
5. Si tot correcte, guardar la proposta per a gestió manual posterior.

### Classificació de `tipus_esdeveniment`
`tipus_esdeveniment` és un string lliure que cal classificar com a **públic** o **privat**, ja que el preu varia. Aquesta classificació és una tasca candidata a automatitzar amb aprenentatge supervisat.

### Finalitat
Ingerir la informació dels correus i guardar-la per a la posterior gestió manual dels esdeveniments. El model **no pren decisions finals**, només estructura i persiste la informació.

### Warning: correus encadenats
Si la informació total arriba en més d'un correu (per exemple, perquè en el primer faltaven dades), cal ser capaç de correlacionar els missatges i completar la fitxa de l'esdeveniment amb les respostes posteriors del sol·licitant.

---

## Estructura del projecte

```
.
├── data/
│   ├── emails.py           # 5 correus de test ficticis
│   ├── agenda.py           # Dates ocupades de l'agenda
│   ├── config.py           # Camps a extreure i camps obligatoris
│   └── ground_truth.py     # Accions esperades per email (per avaluació)
├── src/
│   ├── api_disponibilitat.py  # API de consulta de disponibilitat
│   └── utils.py               # Flux determinista i mètriques compartides
├── experiments/
│   ├── solucio_a/          # Agent autònom amb tool calling
│   ├── solucio_b/          # LLM parser + flux determinista (prompt bàsic)
│   └── solucio_b_v2/       # LLM parser + flux determinista (prompt millorat)
├── resultats.ipynb         # Notebook: executa experiments i mostra gràfiques
└── .env                    # GEMINI_API_KEY
```

Cada carpeta d'experiment conté:
- `experiment.py` — script executable amb `--model` i `--backend` (local/cloud)
- `result_{model}.json` — resultats generats en l'última execució

---

## Requisits previs

- Python 3.10 o superior
- [Ollama](https://ollama.com) per a models locals

---

## Instal·lació

```bash
# Clonar i crear entorn virtual
python -m venv venv && source venv/bin/activate

# Dependències
pip install ollama python-dotenv google-generativeai jupyter matplotlib

# Models locals
ollama pull phi3          # 2.2 GB — Solució B (no suporta tool calling)
ollama pull llama3.2      # 2.0 GB — Solucions A i B
ollama pull qwen2.5:7b    # 4.7 GB — Solucions A i B (millor qualitat)
```

---

## Configuració

Edita `.env` per afegir la teva clau de Gemini (opcional, per al backend cloud):

```
GEMINI_API_KEY=la_teva_clau
```

---

## Execució

### Des del notebook (recomanat)

Obre `resultats.ipynb` i executa totes les cel·les. El notebook:
1. Executa els 3 experiments × 4 models (phi3, llama3.2, qwen2.5:7b, gemini)
2. Guarda els resultats com a `result_{model}.json` a cada carpeta
3. Mostra gràfiques comparatives

### Des de la línia de comandes

```bash
# Solució B amb qwen2.5:7b (local)
python experiments/solucio_b_v2/experiment.py --model qwen2.5:7b --backend local

# Solució B amb Gemini (cloud)
python experiments/solucio_b/experiment.py --model gemini-2.0-flash --backend cloud

# Solució A amb llama3.2
python experiments/solucio_a/experiment.py --model llama3.2 --backend local
```

---

## Resum de compatibilitat

| Model | Sol. A (tool calling) | Sol. B (parser) | Mida |
|---|---|---|---|
| phi3 | ✗ | ✓ | 2.2 GB |
| llama3.2 | ✓ (inconsistent) | ✓ | 2.0 GB |
| qwen2.5:7b | ✓ | ✓ (millor qualitat) | 4.7 GB |
| gemini-2.0-flash | ✓ | ✓ | cloud |
