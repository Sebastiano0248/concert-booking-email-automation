# Automatització de la gestió de correus de contractació de concerts

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
  "dia": "2026-06-15",
  "lloc": "Girona",
  "tipus_esdeveniment": "festa major",
  "usuari": "Ajuntament de Girona",
  "informacio_faltant": ["aforament", "pressupost"]
}
```

El LLM **no pren decisions**: només entén el text lliure i el transforma en dades.

### Capa 2 — Decisió (flux determinista)
A partir de les dades estructurades, un flux fix executa les accions corresponents:

- Si hi ha `informacio_faltant` → enviar resposta automàtica al client demanant les dades
- Si hi ha `data` → comprovar el calendari
- Si la data és lliure i tot correcte → guardar la proposta per a gestió manual

Aquest flux pot implementar-se en codi Python (com en aquest PoC) o amb eines visuals
com **n8n** o **Make.com**. Aquestes eines permeten construir el flux arrossegant nodes,
sense escriure codi, i integren directament amb Gmail, Google Sheets, Slack, Notion, etc.
Això fa que l'equip pugui modificar les regles o afegir passos (per exemple, notificar
per Slack quan arriba una proposta nova) sense tocar el codi de parsing.

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
| `llengua` | No | Llengua principal del correu (ca/es/fr/en) |

### Flux esperat
1. Extreure les dades del correu.
2. Si falta informació obligatòria (`dia`, `lloc`, `tipus_esdeveniment`, `usuari`), demanar-la per correu.
3. Comprovar disponibilitat de la data a l'agenda.
4. Si la data és ocupada, notificar al sol·licitant.
5. Si tot correcte, guardar la proposta per a gestió manual posterior.

### Classificació de `tipus_esdeveniment`
`tipus_esdeveniment` és un string lliure extret del correu (per exemple: *"festa major"*,
*"sopar de gala"*, *"concert de Nadal"*). Cal classificar-lo com a **públic** o **privat**,
ja que el preu de l'actuació és diferent.

Ara mateix, la classificació es fa en el mateix prompt de parsing, demanant al LLM que
inferi el tipus a partir del context. Això funciona raonablement bé, però és una tasca
candidata a separar i automatitzar millor: el volum de sol·licituds eventuals permettria
entrenar un classificador supervisat senzill sobre exemples etiquetats, que seria més
fiable i auditable que deixar-ho a criteri del LLM en cada crida.

### Correus encadenats
En molts casos reals, la informació necessària **no arriba en un sol correu**. El flux
típic és:

1. El client envia un primer correu amb informació incompleta.
2. El sistema detecta la informació faltant i envia una resposta demanant les dades.
3. El client respon amb les dades que faltaven, sovint sense repetir les que ja havia donat.

Això implica que el sistema hauria de ser capaç de **correlacionar missatges d'un mateix
fil** (per assumpte, per adreça del remitent, o per thread ID si el proveïdor de correu
ho exposa) i combinar la informació de tots els missatges per construir una fitxa completa
de l'event. Sense això, la resposta del client es processaria com un correu nou i
independent, i tornaria a detectar informació faltant.

Aquest problema no està resolt en el PoC actual, que tracta cada correu de forma
independent.

### Finalitat
Ingerir la informació dels correus i guardar-la per a la posterior gestió manual dels
esdeveniments. El model **no pren decisions finals**, només estructura i persiste la
informació.

---

## Tasques pendents

- **Gestió de correus encadenats** — correlacionar missatges d'un mateix fil i combinar
  la informació de diverses respostes per construir la fitxa completa d'un event.

- **Classificació automatitzada de `tipus_esdeveniment`** — separar la classificació
  públic/privat del prompt de parsing i implementar-la com un classificador supervisat
  entrenat sobre exemples etiquetats.

- **Integració amb n8n o Make.com** — substituir o complementar el flux determinista
  de Python per un flux visual que integri directament amb Gmail, Google Sheets i Slack,
  sense necessitat de codi per als canvis de regles.

- **Robustesa multilingüe** — els models petits (phi3, llama3.2) cometen errors d'extracció
  quan el correu és en català o francès: confonen camps, translitesen malament noms propis
  o simplement ignoren parts del text. Cal avaluar si el problema es resol amb models més
  grans, amb un prompt en la mateixa llengua que el correu (detectada prèviament), o
  normalitzant els correus a una sola llengua abans del parsing.

- **RAG sobre l'historial de sol·licituds** — donar al LLM accés al historial de
  propostes anteriors per contextualitzar millor les noves sol·licituds.

- **Fine-tuning amb dades reals** — un cop es disposin de correus reals etiquetats,
  afinar el model de parsing per millorar la precisió en l'extracció de camps.

---

## Estructura del projecte

```
.
├── data/
│   ├── emails.py              # 5 correus de test ficticis
│   ├── agenda.py              # Dates ocupades de l'agenda
│   ├── config.py              # Camps a extreure i camps obligatoris
│   └── ground_truth.py        # Accions esperades per email (per avaluació)
├── experiments/
│   ├── solucio_a.py           # Agent autònom amb tool calling
│   ├── solucio_b.py           # LLM parser + flux determinista (prompt bàsic)
│   └── solucio_b_v2.py        # LLM parser + flux determinista (prompt millorat)
├── model_statistics/          # Resultats JSON i gràfiques PNG de les execucions
├── chat_test/
│   ├── chat_test.py           # Servidor web per provar el parsing interactivament
│   └── Examples.md            # Correus de mostra per al chat
├── src/
│   ├── api_disponibilitat.py  # API de consulta de disponibilitat
│   └── utils.py               # Flux determinista i mètriques compartides
├── resultats.ipynb            # Notebook: executa experiments i mostra gràfiques
├── .env.example               # Plantilla de variables d'entorn
└── .env                       # GEMINI_API_KEY (no inclòs al repo)
```

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

Copia `.env.example` a `.env` i afegeix la teva clau de Gemini (opcional, per al backend cloud):

```
GEMINI_API_KEY=la_teva_clau
```

---

## Execució

### Des del notebook (recomanat)

Obre `resultats.ipynb` i executa totes les cel·les. El notebook:
1. Executa els 3 experiments × 4 models (phi3, llama3.2, qwen2.5:7b, gemini)
2. Guarda els resultats com a JSON a `model_statistics/`
3. Mostra gràfiques comparatives

### Des de la línia de comandes

```bash
# Solució B amb qwen2.5:7b (local)
python experiments/solucio_b_v2.py --model qwen2.5:7b --backend local

# Solució B amb Gemini (cloud)
python experiments/solucio_b.py --model gemini-2.0-flash --backend cloud

# Solució A amb llama3.2
python experiments/solucio_a.py --model llama3.2 --backend local
```

---

## Resum de compatibilitat

| Model | Sol. A (tool calling) | Sol. B (parser) | Mida |
|---|---|---|---|
| phi3 | ✗ | ✓ | 2.2 GB |
| llama3.2 | ✓ (inconsistent) | ✓ | 2.0 GB |
| qwen2.5:7b | ✓ | ✓ (millor qualitat) | 4.7 GB |
| gemini-2.0-flash | ✓ | ✓ | cloud |
