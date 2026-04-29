#!/usr/bin/env python3
"""
chat_experiments.py — Web chat per a la gestió de correus de concerts.

Configuració al .env:
    EXPERIMENT=B_v2          # A, B o B_v2
    MODEL=qwen2.5:7b         # phi3 | llama3.2 | qwen2.5:7b | gemini-2.0-flash
    CHAT_HOST=127.0.0.1      # opcional
    CHAT_PORT=5000            # opcional

Executa: python chat_experiments.py
"""
import inspect, json, os, sys, threading
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.api_disponibilitat import consultar_disponibilitat_data
from src.utils import executar_flux, sanititzar_dades, identificar_info_faltant
from data.config import CAMPS_TOTS, CAMPS_REQUERITS

# ── Configuració ──────────────────────────────────────────────────────────────
EXPERIMENT = os.getenv("EXPERIMENT", "B_v2")   # A | B | B_v2
MODEL      = os.getenv("MODEL", "qwen2.5:7b")
BACKEND    = "cloud" if MODEL == "gemini-2.0-flash" else "local"
HOST       = os.getenv("CHAT_HOST", "127.0.0.1")
PORT       = int(os.getenv("CHAT_PORT", "5000"))
MAX_ITER   = 10

NOMS_CAMPS = {
    "dia":               "la data de l'event",
    "lloc":              "el lloc o espai de l'event",
    "tipus_esdeveniment":"el tipus d'event (concert, festival, privat, etc.)",
    "usuari":            "el nom de l'entitat o persona sol·licitant",
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_disponibilitat_data",
            "description": "Comprova si una data concreta ja té una actuació programada.",
            "parameters": {
                "type": "object",
                "properties": {"data": {"type": "string", "description": "Data YYYY-MM-DD"}},
                "required": ["data"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_resposta",
            "description": "Envia una resposta al client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipus": {
                        "type": "string",
                        "enum": ["info_faltant", "guardar", "denegacio_data"],
                    },
                    "missatge": {"type": "string"},
                },
                "required": ["tipus", "missatge"],
            },
        },
    },
]

TIPUS_TO_ACCIO = {
    "info_faltant":  "demanar_info",
    "guardar":       "guardar",
    "denegacio_data":"denegar_data",
}

EINES = {
    "consultar_disponibilitat_data": lambda **kw: json.dumps(
        consultar_disponibilitat_data(**kw), ensure_ascii=False
    ),
    "enviar_resposta": lambda tipus, missatge: json.dumps(
        {"estat": "enviat", "tipus": tipus}, ensure_ascii=False
    ),
}

# ── Estat global (app local, un sol usuari) ───────────────────────────────────
_state: dict = {"conversa": [], "agent_state": {}, "finalitzada": False}

# ── LLM: extracció JSON ───────────────────────────────────────────────────────
def _extraure_json_ollama(prompt: str) -> tuple[dict, bool]:
    import ollama
    resp = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}], format="json")
    try:
        raw = json.loads(resp.message.content)
        return sanititzar_dades(raw), set(CAMPS_TOTS).issubset(set(raw.keys()))
    except json.JSONDecodeError:
        return {}, False


def _extraure_json_gemini(prompt: str) -> tuple[dict, bool]:
    import time, google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    m = genai.GenerativeModel(MODEL, generation_config={"response_mime_type": "application/json"})
    for attempt in range(4):
        try:
            raw = json.loads(m.generate_content(prompt).text)
            return sanititzar_dades(raw), set(CAMPS_TOTS).issubset(set(raw.keys()))
        except json.JSONDecodeError:
            return {}, False
        except Exception as e:
            if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                time.sleep(65 * (attempt + 1))
            else:
                raise
    return {}, False


def _extraure_json(prompt: str) -> tuple[dict, bool]:
    return _extraure_json_ollama(prompt) if BACKEND == "local" else _extraure_json_gemini(prompt)


# ── LLM: generació text lliure ────────────────────────────────────────────────
def _generar_text_ollama(prompt: str) -> str:
    import ollama
    return ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}]).message.content.strip()


def _generar_text_gemini(prompt: str) -> str:
    import time, google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    m = genai.GenerativeModel(MODEL)
    for attempt in range(4):
        try:
            return m.generate_content(prompt).text.strip()
        except Exception as e:
            if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                time.sleep(65 * (attempt + 1))
            else:
                raise
    return ""


def _generar_text(prompt: str) -> str:
    return _generar_text_ollama(prompt) if BACKEND == "local" else _generar_text_gemini(prompt)


# ── LLM: loop agent (Solució A) ───────────────────────────────────────────────
def _agent_loop_ollama(historial: list) -> tuple[str, str, list, list]:
    import ollama
    accio, missatge, tool_log = "fallada", "", []
    for _ in range(MAX_ITER):
        resp = ollama.chat(model=MODEL, messages=historial, tools=TOOLS_SCHEMA)
        msg = resp.message
        historial.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls or []})
        if not msg.tool_calls:
            break
        resposta_enviada = False
        for tc in msg.tool_calls:
            nom  = tc.function.name
            args = tc.function.arguments or {}
            if nom in EINES:
                func  = EINES[nom]
                sig   = inspect.signature(func)
                args_v = {k: v for k, v in args.items() if k in sig.parameters}
                try:
                    res = func(**args_v)
                    if nom == "enviar_resposta":
                        accio   = TIPUS_TO_ACCIO.get(args_v.get("tipus", ""), "desconegut")
                        missatge = args_v.get("missatge", "")
                        resposta_enviada = True
                    tool_log.append({"nom": nom, "args": args_v, "resultat": json.loads(res)})
                except Exception as e:
                    res = json.dumps({"error": str(e)})
                    tool_log.append({"nom": nom, "args": args_v, "error": str(e)})
            else:
                res = json.dumps({"error": f"Eina '{nom}' no trobada"})
            historial.append({"role": "tool", "content": res})
        if resposta_enviada:
            break
    return accio, missatge, historial, tool_log


def _agent_loop_gemini(last_resp, chat) -> tuple[str, str, list]:
    import time
    import google.generativeai.protos as protos
    accio, missatge, tool_log = "fallada", "", []
    for _ in range(MAX_ITER):
        fn_calls = [
            p.function_call
            for cand in last_resp.candidates
            for p in cand.content.parts
            if hasattr(p, "function_call") and p.function_call.name
        ]
        if not fn_calls:
            break
        parts_resp = []
        resposta_enviada = False
        for fc in fn_calls:
            nom, args = fc.name, dict(fc.args)
            if nom in EINES:
                try:
                    res = EINES[nom](**args)
                    if nom == "enviar_resposta":
                        accio    = TIPUS_TO_ACCIO.get(args.get("tipus", ""), "desconegut")
                        missatge = args.get("missatge", "")
                        resposta_enviada = True
                    tool_log.append({"nom": nom, "args": args, "resultat": json.loads(res)})
                except Exception as e:
                    res = json.dumps({"error": str(e)})
                    tool_log.append({"nom": nom, "args": args, "error": str(e)})
            else:
                res = json.dumps({"error": f"Eina '{nom}' no trobada"})
            parts_resp.append(protos.Part(
                function_response=protos.FunctionResponse(name=nom, response={"result": res})
            ))
        for attempt in range(4):
            try:
                last_resp = chat.send_message(protos.Content(parts=parts_resp, role="user"))
                break
            except Exception as e:
                if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                    time.sleep(65 * (attempt + 1))
                else:
                    raise
        if resposta_enviada:
            break
    return accio, missatge, tool_log


# ── Prompts ───────────────────────────────────────────────────────────────────
def _prompt_extraccio(conversa: list) -> str:
    instr = (
        "Infereix el camp si apareix de manera implícita: p.ex. el lloc des del nom "
        "de l'entitat o del domini del correu, o el tipus_esdeveniment des del context."
        if EXPERIMENT == "B_v2" else
        "Extreu únicament el que diu explícitament el text."
    )
    blocs = []
    for m in conversa:
        prefix = "[MISSATGE DEL CLIENT]" if m["role"] == "user" else "[RESPOSTA DE L'ASSISTENT]"
        blocs.append(f"{prefix}\n{m['content']}")
    return (
        "Analitza la CONVERSA COMPLETA i extreu la informació en format JSON.\n"
        + instr + "\n"
        "Si un camp no apareix en cap missatge, posa null. Dates en format YYYY-MM-DD.\n\n"
        "Camps (retorna exactament aquestes claus):\n"
        "- dia: data concreta de l'event (YYYY-MM-DD o null)\n"
        "- lloc: ciutat o espai (string o null)\n"
        "- tipus_esdeveniment: tipus d'event (string o null)\n"
        "- usuari: nom de l'entitat o persona sol·licitant (string o null)\n"
        "- durada: durada estimada (string o null)\n"
        "- aforament: capacitat de l'espai (integer o null)\n"
        "- pressupost: pressupost mencionat (string o null)\n"
        "- llengua: llengua principal del correu (ca/es/fr/en)\n\n"
        "CONVERSA:\n"
        + "\n\n".join(blocs)
        + "\n\nRespon ÚNICAMENT amb el JSON, sense cap text addicional."
    )


def _prompt_resposta(dades: dict, camps_faltants: list, primer_missatge: str) -> str:
    noms = [NOMS_CAMPS.get(c, c) for c in camps_faltants]
    dades_ok = {k: v for k, v in dades.items() if v is not None}
    return (
        "Ets l'assistent de gestió d'actuacions musicals.\n"
        f"Has rebut aquest missatge del client:\n\n{primer_missatge}\n\n"
        f"Has extret les dades: {json.dumps(dades_ok, ensure_ascii=False)}\n"
        f"Falta informació obligatòria: {', '.join(noms)}.\n\n"
        "Redacta una resposta breu (3-4 frases) en el MATEIX idioma que el missatge del client, "
        "demanant amablement la informació que falta. "
        "Respon ÚNICAMENT amb el text de la resposta."
    )


# ── Lògica dels experiments ───────────────────────────────────────────────────
def run_sol_b(conversa: list) -> dict:
    pr_ext = _prompt_extraccio(conversa)
    dades, json_valid = _extraure_json(pr_ext)
    accio = executar_flux(dades)

    detalls: dict = {
        "prompt_extraccio": pr_ext,
        "dades_extretes":   dades,
        "json_valid":       json_valid,
    }

    if accio == "demanar_info":
        camps_f   = identificar_info_faltant(dades)
        pr_resp   = _prompt_resposta(dades, camps_f, conversa[0]["content"])
        missatge  = _generar_text(pr_resp)
        detalls["prompt_resposta"]  = pr_resp
        detalls["camps_faltants"]   = camps_f
    elif accio == "denegar_data":
        data     = dades.get("dia", "la data sol·licitada")
        missatge = (f"Lamentem informar-vos que la data {data} no està disponible. "
                    "Podeu proposar-nos una altra data alternativa?")
    else:
        usuari   = dades.get("usuari", "vosaltres")
        data     = dades.get("dia", "")
        lloc     = dades.get("lloc", "")
        missatge = (f"Perfecte! Hem registrat la sol·licitud de {usuari} per al {data} a {lloc}. "
                    "Ens posarem en contacte per confirmar tots els detalls.")

    return {"missatge": missatge, "accio": accio, "detalls": detalls}


def run_sol_a(conversa: list, agent_state: dict) -> dict:
    sys_prompt = (
        "Ets l'assistent de gestió de concerts d'una associació musical. "
        "Per a cada missatge: comprova si tens dia, lloc, tipus_esdeveniment i usuari. "
        "Si en falta algun, usa enviar_resposta(tipus='info_faltant') explicant quina "
        "informació falta i demanant-la en el mateix idioma que el client. "
        "Si tens tota la informació, usa consultar_disponibilitat_data per comprovar la data. "
        "Si la data és lliure, usa enviar_resposta(tipus='guardar'). "
        "Si la data és ocupada, usa enviar_resposta(tipus='denegacio_data')."
    )

    if not agent_state.get("inicialitzat"):
        if BACKEND == "local":
            agent_state["historial"] = [
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": conversa[-1]["content"]},
            ]
        else:
            agent_state["system_prompt"]   = sys_prompt
            agent_state["primer_missatge"] = conversa[-1]["content"]
        agent_state["inicialitzat"] = True
    elif BACKEND == "local":
        agent_state["historial"].append({"role": "user", "content": conversa[-1]["content"]})

    if BACKEND == "local":
        accio, missatge, hist_nou, tool_log = _agent_loop_ollama(agent_state["historial"])
        agent_state["historial"] = hist_nou
        hist_display = [{"role": m["role"], "content": m.get("content") or ""} for m in hist_nou]
    else:
        import time, google.generativeai as genai, google.generativeai.protos as protos
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        fdecls = [
            protos.FunctionDeclaration(
                name="consultar_disponibilitat_data",
                description="Comprova si una data concreta ja té una actuació programada.",
                parameters=protos.Schema(
                    type=protos.Type.OBJECT,
                    properties={"data": protos.Schema(type=protos.Type.STRING, description="Data YYYY-MM-DD")},
                    required=["data"],
                ),
            ),
            protos.FunctionDeclaration(
                name="enviar_resposta",
                description="Envia una resposta al client.",
                parameters=protos.Schema(
                    type=protos.Type.OBJECT,
                    properties={
                        "tipus":   protos.Schema(type=protos.Type.STRING,
                                                 enum=["info_faltant", "guardar", "denegacio_data"]),
                        "missatge": protos.Schema(type=protos.Type.STRING),
                    },
                    required=["tipus", "missatge"],
                ),
            ),
        ]
        if not agent_state.get("chat"):
            gm   = genai.GenerativeModel(MODEL, tools=[protos.Tool(function_declarations=fdecls)])
            chat = gm.start_chat()
            for attempt in range(4):
                try:
                    last = chat.send_message(f"{sys_prompt}\n\n{agent_state['primer_missatge']}")
                    break
                except Exception as e:
                    if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                        time.sleep(65 * (attempt + 1))
                    else:
                        raise
            agent_state["chat"] = chat
            agent_state["last"] = last
        else:
            for attempt in range(4):
                try:
                    agent_state["last"] = agent_state["chat"].send_message(conversa[-1]["content"])
                    break
                except Exception as e:
                    if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                        time.sleep(65 * (attempt + 1))
                    else:
                        raise
        accio, missatge, tool_log = _agent_loop_gemini(agent_state["last"], agent_state["chat"])
        hist_display = [
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": agent_state.get("primer_missatge", "")},
        ]

    if not missatge and accio == "fallada":
        missatge = "L'agent no ha pogut processar el missatge. Torneu-ho a intentar."

    detalls = {"tool_log": tool_log, "historial": hist_display, "system_prompt": sys_prompt}
    return {"missatge": missatge, "accio": accio, "detalls": detalls, "agent_state": agent_state}


# ── Flask ─────────────────────────────────────────────────────────────────────
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return HTML_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.post("/chat")
def chat():
    text = (request.json or {}).get("missatge", "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Missatge buit"}), 400
    if _state["finalitzada"]:
        return jsonify({"ok": False, "error": "Conversa finalitzada. Prem Nova conversa."}), 400

    _state["conversa"].append({"role": "user", "content": text})
    try:
        if EXPERIMENT == "A":
            result = run_sol_a(_state["conversa"], _state["agent_state"])
            _state["agent_state"] = result["agent_state"]
        else:
            result = run_sol_b(_state["conversa"])

        _state["conversa"].append({"role": "assistant", "content": result["missatge"]})
        if result["accio"] in ("guardar", "denegar_data"):
            _state["finalitzada"] = True

        return jsonify({
            "ok":         True,
            "missatge":   result["missatge"],
            "accio":      result["accio"],
            "finalitzada":_state["finalitzada"],
            "detalls":    result["detalls"],
        })
    except Exception as e:
        _state["conversa"].pop()
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/reset")
def reset():
    _state.update({"conversa": [], "agent_state": {}, "finalitzada": False})
    return jsonify({"ok": True})


@app.get("/state")
def state():
    return jsonify({
        "conversa":    _state["conversa"],
        "finalitzada": _state["finalitzada"],
        "experiment":  EXPERIMENT,
        "model":       MODEL,
        "backend":     BACKEND,
    })


# ── Pàgina HTML ───────────────────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chat Experiments — Concerts</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0d0821;height:100dvh;display:flex;flex-direction:column;overflow:hidden;color:#e9e4ff}

/* Header */
.hdr{background:linear-gradient(135deg,#3b1fa8,#6d1fd6);color:#fff;padding:10px 18px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;box-shadow:0 2px 16px rgba(109,31,214,.45)}
.hdr-title{font-size:1rem;font-weight:600;letter-spacing:.01em}
.hdr-info{font-size:.75rem;opacity:.78;margin-top:2px;color:#c4b5fd}
.btn-reset{background:rgba(255,255,255,.12);color:#e9d5ff;border:1px solid rgba(196,165,253,.4);padding:5px 13px;border-radius:6px;cursor:pointer;font-size:.82rem;transition:background .2s}
.btn-reset:hover{background:rgba(255,255,255,.22)}

/* Chat */
.chat{flex:1;overflow-y:auto;padding:14px 18px;display:flex;flex-direction:column;gap:10px}
.chat::-webkit-scrollbar{width:5px}
.chat::-webkit-scrollbar-track{background:transparent}
.chat::-webkit-scrollbar-thumb{background:#3b1fa8;border-radius:4px}

/* Missatges */
.mw{display:flex;flex-direction:column;max-width:80%}
.mw.u{align-self:flex-end;align-items:flex-end}
.mw.a{align-self:flex-start;align-items:flex-start}
.lbl{font-size:.7rem;color:#9b87d8;margin-bottom:2px;padding:0 4px}
.bubble{padding:9px 13px;border-radius:18px;font-size:.875rem;line-height:1.5;white-space:pre-wrap;word-break:break-word}
.mw.u .bubble{background:linear-gradient(135deg,#6d1fd6,#c026d3);color:#fff;border-radius:18px 18px 4px 18px;box-shadow:0 2px 12px rgba(192,38,211,.35)}
.mw.a .bubble{background:#1e1245;color:#e9e4ff;border-radius:18px 18px 18px 4px;border:1px solid #3b2570;box-shadow:0 1px 6px rgba(0,0,0,.3)}

/* Badge */
.badge{display:inline-block;font-size:.7rem;font-weight:600;padding:2px 10px;border-radius:20px;margin-top:5px}
.badge.guardar{background:#14532d;color:#86efac;border:1px solid #166534}
.badge.denegar_data{background:#4c0519;color:#fca5a5;border:1px solid #7f1d1d}
.badge.demanar_info{background:#3b1f07;color:#fcd34d;border:1px solid #78350f}
.badge.fallada{background:#1e1245;color:#9b87d8;border:1px solid #3b2570}

/* Details */
details{margin-top:5px;background:#1a0d3e;border:1px solid #3b2570;border-radius:10px;overflow:hidden;font-size:.8rem;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:600px}
summary{cursor:pointer;padding:7px 12px;color:#c4b5fd;font-weight:500;user-select:none;list-style:none;display:flex;align-items:center;gap:5px}
summary::-webkit-details-marker{display:none}
summary::before{content:'▶';font-size:.65rem;transition:transform .2s;flex-shrink:0;color:#9b87d8}
details[open] summary::before{transform:rotate(90deg)}
.det-body{padding:10px 14px;border-top:1px solid #3b2570;display:flex;flex-direction:column;gap:10px}
.det-sec h4{font-size:.68rem;font-weight:700;text-transform:uppercase;color:#9b87d8;letter-spacing:.06em;margin-bottom:5px}
.det-sec pre{background:#110828;border:1px solid #2d1b69;border-radius:6px;padding:9px;overflow:auto;font-size:.75rem;line-height:1.55;white-space:pre-wrap;word-break:break-word;color:#c4b5fd;max-height:260px}
.tool-item{background:#110828;border:1px solid #2d1b69;border-radius:6px;padding:7px 10px;font-size:.75rem;margin-top:4px;color:#c4b5fd}
.tool-name{font-weight:600;color:#a855f7}

/* Input */
.inp-area{background:#130a30;border-top:1px solid #2d1b69;padding:10px 18px;display:flex;gap:9px;align-items:flex-end;flex-shrink:0}
textarea{flex:1;resize:none;border:1px solid #3b2570;border-radius:10px;padding:9px 13px;font-size:.875rem;line-height:1.45;font-family:inherit;outline:none;transition:border-color .2s,box-shadow .2s;min-height:42px;max-height:150px;overflow-y:auto;background:#1a0d3e;color:#e9e4ff}
textarea::placeholder{color:#6b4fa8}
textarea:focus{border-color:#a855f7;box-shadow:0 0 0 3px rgba(168,85,247,.2)}
.btn-send{background:linear-gradient(135deg,#6d1fd6,#c026d3);color:#fff;border:none;border-radius:10px;padding:0 18px;font-size:.875rem;font-weight:500;cursor:pointer;transition:opacity .2s,box-shadow .2s;flex-shrink:0;height:42px;box-shadow:0 2px 10px rgba(192,38,211,.4)}
.btn-send:hover{opacity:.88;box-shadow:0 4px 16px rgba(192,38,211,.55)}
.btn-send:disabled{background:#2d1b69;color:#6b4fa8;box-shadow:none;cursor:not-allowed}

.fin-banner{text-align:center;padding:10px 16px;border-radius:10px;font-size:.83rem;color:#9b87d8;background:#1a0d3e;border:1px solid #3b2570;flex-shrink:0;margin:0 18px 12px}
.err{color:#f87171;font-size:.8rem;padding:4px 8px;align-self:center}
</style>
</head>
<body>

<div class="hdr">
  <div>
    <div class="hdr-title">💬 Chat Experiments — Correus de concerts</div>
    <div class="hdr-info" id="hdr-info">…</div>
  </div>
  <button class="btn-reset" onclick="resetChat()">↺ Nova conversa</button>
</div>

<div class="chat" id="chat"></div>

<div class="inp-area">
  <textarea id="inp" placeholder="Escriu el correu o la resposta aquí… (Intro per enviar, Shift+Intro per saltar línia)"
            onkeydown="onKey(event)" oninput="resize(this)"></textarea>
  <button class="btn-send" id="send-btn" onclick="send()">Enviar</button>
</div>

<script>
const chatEl  = document.getElementById('chat');
const inp     = document.getElementById('inp');
const sendBtn = document.getElementById('send-btn');
let finalitzada = false;

/* ── Init ── */
fetch('/state').then(r=>r.json()).then(s=>{
  document.getElementById('hdr-info').textContent =
    `Experiment: ${s.experiment}  |  Model: ${s.model}  (${s.backend})`;
  finalitzada = s.finalitzada;
  s.conversa.forEach(m => {
    if (m.role==='user')      addUser(m.content);
    if (m.role==='assistant') addAssistant(m.content, null, null);
  });
  if (finalitzada) lockInput();
  scrollBot();
});

/* ── Missatges ── */
function addUser(text) {
  const d = el('div','mw u');
  d.innerHTML = `<div class="lbl">Tu</div><div class="bubble">${esc(text)}</div>`;
  chatEl.appendChild(d);
}

function addAssistant(text, accio, detalls) {
  const d = el('div','mw a');
  let h = `<div class="lbl">Assistent</div><div class="bubble">${esc(text)}</div>`;
  if (accio)   h += `<span class="badge ${accio}">${badgeTxt(accio)}</span>`;
  if (detalls) h += buildDetails(detalls);
  d.innerHTML = h;
  chatEl.appendChild(d);
}

function buildDetails(det) {
  let h = '<details><summary>🔍 Detalls de la resposta</summary><div class="det-body">';

  if (det.dades_extretes !== undefined) {
    h += sec('Dades extretes (JSON)', JSON.stringify(det.dades_extretes, null, 2));
  }
  if (det.camps_faltants && det.camps_faltants.length) {
    h += sec('Camps obligatoris faltants', det.camps_faltants.join(', '));
  }
  if (det.prompt_extraccio) {
    h += sec("Prompt d'extracció → LLM", det.prompt_extraccio);
  }
  if (det.prompt_resposta) {
    h += sec('Prompt de resposta → LLM', det.prompt_resposta);
  }
  if (det.tool_log && det.tool_log.length) {
    let tools = '<div class="det-sec"><h4>Eines cridades per l\'agent</h4>';
    det.tool_log.forEach(t => {
      tools += `<div class="tool-item">
        <span class="tool-name">${esc(t.nom)}</span>
        <span style="color:#555"> args: </span><code>${esc(JSON.stringify(t.args))}</code><br>
        <span style="color:#555"> resultat: </span><code>${esc(JSON.stringify(t.resultat??t.error))}</code>
      </div>`;
    });
    tools += '</div>';
    h += tools;
  }
  if (det.system_prompt) {
    h += sec('System prompt de l\'agent', det.system_prompt);
  }
  if (det.historial && det.historial.length) {
    const sum = det.historial.map(m=>`[${m.role}] ${(m.content||'').slice(0,120)}`).join('\n');
    h += sec('Historial de missatges (resum)', sum);
  }

  h += '</div></details>';
  return h;
}

function sec(title, content) {
  return `<div class="det-sec"><h4>${esc(title)}</h4><pre>${esc(content)}</pre></div>`;
}

function badgeTxt(a) {
  return {guardar:'✅ Guardat',denegar_data:'❌ Data ocupada',
          demanar_info:'ℹ️ Informació necessària',fallada:'⚠️ Error'}[a]||a;
}

/* ── Accions ── */
async function send() {
  const text = inp.value.trim();
  if (!text || finalitzada) return;
  inp.value = ''; resize(inp);
  addUser(text); scrollBot();
  setLoad(true);

  try {
    const r    = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({missatge:text})});
    const data = await r.json();
    if (!data.ok) {
      addErr(data.error);
    } else {
      addAssistant(data.missatge, data.accio, data.detalls);
      if (data.finalitzada) { finalitzada=true; lockInput(); }
    }
  } catch(e) { addErr('Error de connexió: '+e.message); }

  setLoad(false); scrollBot();
}

async function resetChat() {
  await fetch('/reset',{method:'POST'});
  chatEl.innerHTML='';
  finalitzada=false;
  inp.disabled=false; sendBtn.disabled=false; sendBtn.textContent='Enviar';
  inp.value=''; inp.focus();
  const fb = document.querySelector('.fin-banner');
  if (fb) fb.remove();
}

function lockInput() {
  inp.disabled=true; sendBtn.disabled=true;
  const b=el('div','fin-banner');
  b.textContent="Conversa finalitzada. Prem 'Nova conversa' per reiniciar.";
  document.body.insertBefore(b, document.querySelector('.inp-area'));
}

/* ── Utils ── */
function el(tag,cls){const d=document.createElement(tag);d.className=cls;return d}
function addErr(msg){const d=el('div','err');d.textContent='❌ '+msg;chatEl.appendChild(d);}
function setLoad(on){sendBtn.disabled=on;sendBtn.textContent=on?'…':'Enviar'}
function scrollBot(){chatEl.scrollTop=chatEl.scrollHeight}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}
function resize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,150)+'px'}
</script>
</body>
</html>
"""

# ── Warmup Ollama ─────────────────────────────────────────────────────────────
def _warmup():
    if BACKEND != "local":
        return
    try:
        import ollama
        print(f"  Carregant model {MODEL} en memòria...", end="", flush=True)
        ollama.chat(model=MODEL, messages=[{"role": "user", "content": "ok"}])
        print(" llest ✓")
    except Exception as e:
        print(f"\n  Avís warmup: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Chat Experiments — Correus de Concerts ===")
    print(f"  Experiment : {EXPERIMENT}")
    print(f"  Model      : {MODEL}  ({BACKEND})")
    _warmup()
    print(f"\n  Obert a:  http://{HOST}:{PORT}")
    print("  Ctrl+C per aturar\n")
    app.run(host=HOST, port=PORT, debug=False)
