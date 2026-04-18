"""
EXPERIMENT: Solució A — Agent autònom amb tool calling
------------------------------------------------------
El LLM decideix autònomament quines eines cridar.
Eines disponibles: consultar_disponibilitat_data, enviar_resposta.
CLI: python experiment.py --model llama3.2 --backend local
     python experiment.py --model gemini-2.0-flash --backend cloud
"""

import argparse
import inspect
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from data.emails import CORREUS
from data.ground_truth import ACCIO_ESPERADA
from src.api_disponibilitat import consultar_disponibilitat_data
from src.utils import calcular_metriques, guardar_resultat

MAX_ITERACIONS = 10
GEMINI_MODEL   = "gemini-2.0-flash"

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
                        "description": (
                            "info_faltant: falta informació obligatòria (dia, lloc, tipus_esdeveniment, usuari). "
                            "guardar: tota la info present i data disponible → guardar proposta. "
                            "denegacio_data: la data sol·licitada ja està ocupada."
                        ),
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
    "denegacio_data": "denegar_data",
}


def _enviar_resposta_fn(tipus: str, missatge: str) -> str:
    print(f"  >>> [{tipus.upper()}]: {missatge[:80]}...")
    return json.dumps({"estat": "enviat", "tipus": tipus})


EINES_PYTHON = {
    "consultar_disponibilitat_data": lambda **kw: json.dumps(
        consultar_disponibilitat_data(**kw), ensure_ascii=False
    ),
    "enviar_resposta": _enviar_resposta_fn,
}


def _system_prompt() -> str:
    return (
        "Ets l'assistent de gestió de concerts d'una associació musical. "
        "Per a cada correu: comprova si tens dia, lloc, tipus_esdeveniment i usuari. "
        "Si en falta algun, usa enviar_resposta(tipus='info_faltant'). "
        "Si tens tota la informació, usa consultar_disponibilitat_data per comprovar la data. "
        "Si la data és lliure, usa enviar_resposta(tipus='guardar'). "
        "Si la data és ocupada, usa enviar_resposta(tipus='denegacio_data')."
    )


def _user_message(correu: dict) -> str:
    return (
        f"Nou correu rebut:\nDe: {correu['de']}\nAssumpte: {correu['assumpte']}\n"
        f"Cos:\n{correu['cos']}\nGestiona aquest correu."
    )


def _run_ollama_agent(correu: dict, model: str) -> dict:
    import ollama
    historial = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user",   "content": _user_message(correu)},
    ]
    eines_cridades, schema_errors, accio_final, resposta_enviada = [], 0, "fallada", False
    dades_inferides: dict = {}

    for _ in range(MAX_ITERACIONS):
        resp = ollama.chat(model=model, messages=historial, tools=TOOLS_SCHEMA)
        msg  = resp.message
        historial.append({
            "role": "assistant", "content": msg.content or "",
            "tool_calls": msg.tool_calls or [],
        })
        if not msg.tool_calls:
            break

        for tc in msg.tool_calls:
            nom  = tc.function.name
            args = tc.function.arguments or {}
            print(f"  → {nom}({json.dumps(args, ensure_ascii=False)})")
            if nom in EINES_PYTHON:
                func = EINES_PYTHON[nom]
                sig  = inspect.signature(func)
                args_v = {k: v for k, v in args.items() if k in sig.parameters}
                if set(args) - set(sig.parameters):
                    schema_errors += 1
                try:
                    resultat = func(**args_v)
                    eines_cridades.append(nom)
                    if nom == "consultar_disponibilitat_data":
                        dades_inferides["dia"] = args_v.get("data")
                    if nom == "enviar_resposta":
                        accio_final = TIPUS_TO_ACCIO.get(args_v.get("tipus", ""), "desconegut")
                        dades_inferides["missatge_enviat"] = args_v.get("missatge", "")
                        resposta_enviada = True
                except Exception as e:
                    resultat = json.dumps({"error": str(e)})
                    schema_errors += 1
            else:
                resultat = json.dumps({"error": f"Eina '{nom}' no trobada"})
                schema_errors += 1
                print(f"  [ERROR] Eina desconeguda: {nom}")
            historial.append({"role": "tool", "content": resultat})

        if resposta_enviada:
            break

    return {"eines_cridades": eines_cridades, "schema_errors": schema_errors, "accio": accio_final, "dades_inferides": dades_inferides}


def _run_gemini_agent(correu: dict, api_key: str) -> dict:
    import time
    import google.generativeai as genai
    import google.generativeai.protos as protos

    genai.configure(api_key=api_key)
    tools_genai = protos.Tool(function_declarations=[
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
                    "tipus": protos.Schema(
                        type=protos.Type.STRING,
                        enum=["info_faltant", "guardar", "denegacio_data"],
                    ),
                    "missatge": protos.Schema(type=protos.Type.STRING),
                },
                required=["tipus", "missatge"],
            ),
        ),
    ])

    model = genai.GenerativeModel(GEMINI_MODEL, tools=[tools_genai])
    chat  = model.start_chat()

    for attempt in range(4):
        try:
            resp = chat.send_message(f"{_system_prompt()}\n\n{_user_message(correu)}")
            break
        except Exception as e:
            if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                wait = 65 * (attempt + 1)
                print(f"\n  [Quota Gemini] Esperant {wait}s (intent {attempt+1}/3)...")
                time.sleep(wait)
                chat = model.start_chat()
            else:
                raise

    eines_cridades, schema_errors, accio_final, resposta_enviada = [], 0, "fallada", False
    dades_inferides: dict = {}

    for _ in range(MAX_ITERACIONS):
        fn_calls = [
            part.function_call
            for candidate in resp.candidates
            for part in candidate.content.parts
            if hasattr(part, "function_call") and part.function_call.name
        ]
        if not fn_calls:
            break

        parts_resp = []
        for fc in fn_calls:
            nom  = fc.name
            args = dict(fc.args)
            print(f"  → {nom}({json.dumps(args, ensure_ascii=False)})")
            if nom in EINES_PYTHON:
                try:
                    resultat = EINES_PYTHON[nom](**args)
                    eines_cridades.append(nom)
                    if nom == "consultar_disponibilitat_data":
                        dades_inferides["dia"] = args.get("data")
                    if nom == "enviar_resposta":
                        accio_final = TIPUS_TO_ACCIO.get(args.get("tipus", ""), "desconegut")
                        dades_inferides["missatge_enviat"] = args.get("missatge", "")
                        resposta_enviada = True
                except Exception as e:
                    resultat = json.dumps({"error": str(e)})
                    schema_errors += 1
            else:
                resultat = json.dumps({"error": f"Eina '{nom}' no trobada"})
                schema_errors += 1
            parts_resp.append(protos.Part(
                function_response=protos.FunctionResponse(
                    name=nom, response={"result": resultat}
                )
            ))

        for attempt in range(4):
            try:
                resp = chat.send_message(protos.Content(parts=parts_resp, role="user"))
                break
            except Exception as e:
                if attempt < 3 and any(k in str(e) for k in ("quota", "429", "ResourceExhausted")):
                    wait = 65 * (attempt + 1)
                    print(f"\n  [Quota Gemini] Esperant {wait}s (intent {attempt+1}/3)...")
                    time.sleep(wait)
                else:
                    raise
        if resposta_enviada:
            break

    return {"eines_cridades": eines_cridades, "schema_errors": schema_errors, "accio": accio_final, "dades_inferides": dades_inferides}


def _processar_correu(correu: dict, model: str, backend: str, gemini_key: str) -> dict:
    print(f"\n{'='*60}\nCORREU #{correu['id']} — {correu['assumpte']}\n{'='*60}")

    r = _run_ollama_agent(correu, model) if backend == "local" else _run_gemini_agent(correu, gemini_key)

    accio_esp = ACCIO_ESPERADA[correu["id"]]
    print(f"\n>>> ACCIÓ: {r['accio']}  (esperada: {accio_esp})")
    return {
        "id": correu["id"],
        "assumpte": correu["assumpte"],
        "eines_cridades": r["eines_cridades"],
        "tool_schema_errors": r["schema_errors"],
        "json_valid": r["schema_errors"] == 0,
        "dades_extretes": r.get("dades_inferides", {}),
        "camps_extrets": None,
        "camps_disponibles": None,
        "accio": r["accio"],
        "accio_esperada": accio_esp,
        "accio_correcta": r["accio"] == accio_esp,
    }


def run(model: str, backend: str = "local") -> dict:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    if backend == "cloud" and (not gemini_key or gemini_key == "your_api_key_here"):
        raise ValueError("GEMINI_API_KEY no configurada al .env")

    print(f"\nSolució A | Backend: {backend} | Model: {model}")
    resultats  = [_processar_correu(c, model, backend, gemini_key) for c in CORREUS]
    metriques  = calcular_metriques(resultats)
    model_label = model.replace(":", "_").replace(".", "_")
    return {
        "experiment_id": f"solucio_a_{model_label}",
        "solucio": "A",
        "model": model,
        "backend": backend,
        "data": str(date.today()),
        "emails": resultats,
        "metriques": metriques,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",   default="llama3.2")
    p.add_argument("--backend", default="local", choices=["local", "cloud"])
    args = p.parse_args()
    result = run(args.model, args.backend)
    model_label = args.model.replace(":", "_").replace(".", "_")
    guardar_resultat(result, ROOT / "model_statistics" / f"solucio_a_{model_label}.json")
    m = result["metriques"]
    print(f"Accuracy: {m['accuracy']:.0%} | Score: {m['score']:.3f}")
