# langgraph/langgraph_agent.py
import yaml
import threading
import json
from a2a.a2a_protocol import BUS, send_message, A2AMessage
from utils.ollama_client import OllamaClient
from pathlib import Path
from typing import Dict, Any

CFG = yaml.safe_load(open("yaml/langgraph_agent.yaml", "r"))

AGENT_NAME = CFG.get("name", "langgraph_agent")
TARGET_RECEIVER = CFG.get("target_receiver", "monitor_agent")
LISTEN_TYPES = set(CFG.get("listen_message_types", []))
RULES = CFG.get("rules", [])
MODEL = "gemma:2b"

ollama = OllamaClient(model=MODEL)

# helper: simple rule engine
def apply_rules(message: A2AMessage) -> Dict[str, Any]:
    results = {"passed": True, "checks": []}
    payload = message.payload or {}
    ticket_id = payload.get("ticket_id") or payload.get("triage", {}).get("ticket_id") if isinstance(payload.get("triage"), dict) else payload.get("ticket_id")
    
    # Rule: must have ticket_id
    r = {"id":"must_have_ticket_id", "ok": bool(ticket_id), "note": None}
    if not r["ok"]:
        r["note"] = "Missing ticket_id"
        results["passed"] = False
    results["checks"].append(r)
    
    # Rule: troubleshoot step count limit
    if message.type == "troubleshoot_done":
        steps = []
        # payload.result might be a dict or JSON string; attempt parse
        res = payload.get("result")
        if isinstance(res, str):
            try:
                parsed = json.loads(res)
            except Exception:
                parsed = {}
        else:
            parsed = res or {}
        steps = parsed.get("executed_steps") or parsed.get("steps") or []
        cnt = len(steps) if isinstance(steps, list) else 0
        threshold = next((r['threshold'] for r in RULES if r['id']=="max_steps"), 8)
        ok = cnt <= threshold
        rc = {"id":"max_steps", "ok": ok, "note": f"{cnt} steps (threshold {threshold})"}
        if not ok:
            results["passed"] = False
        results["checks"].append(rc)
    
    # Text/safety checks via LLM: detect uncertain definitive claims
    text_to_check = ""
    # try to assemble textual evidence
    if message.type == "retrieval_ready":
        text_to_check = " ".join([str(x.get("content","")) for x in (payload.get("kb_hits") or [])]) + " " + " ".join(payload.get("web_snippets") or [])
    elif message.type == "adk_context":
        text_to_check = str(payload.get("enriched_context") or "")
    elif message.type == "troubleshoot_done":
        text_to_check = str(payload.get("result") or "")
    else:
        text_to_check = str(payload)
    
    prompt = (
        "You are a validation assistant. Inspect the following text and answer in JSON:\n\n"
        f"TEXT: {text_to_check}\n\n"
        "Return JSON with keys: { 'hallucination': true/false, 'uncertain_claims': [ ... ], 'summary': 'short' }\n"
        "Hallucination = claims that cannot be substantiated by KB or are nonsensical.\n"
    )
    try:
        llm_resp = ollama.run(prompt)
        # attempt parse
        parsed = {}
        try:
            parsed = json.loads(llm_resp)
        except Exception:
            # fallback: wrap into note
            parsed = {"hallucination": False, "uncertain_claims": [], "summary": llm_resp[:300]}
    except Exception as e:
        parsed = {"hallucination": False, "uncertain_claims": [], "summary": f"LLM error: {e}"}
    
    results["checks"].append({"id":"llm_validation","ok": not parsed.get("hallucination", False), "note": parsed})
    if parsed.get("hallucination", False):
        results["passed"] = False
    
    return results

def langgraph_loop():
    BUS.register(AGENT_NAME)
    while True:
        msg = BUS.receive(AGENT_NAME, timeout=1)
        if not msg:
            continue
        # only handle defined types
        if msg.type not in LISTEN_TYPES:
            continue
        try:
            outcome = apply_rules(msg)
            decision = {
                "ticket_id": msg.payload.get("ticket_id"),
                "source_type": msg.type,
                "validation": outcome
            }
            send_message(sender=AGENT_NAME, receiver=TARGET_RECEIVER, type=CFG.get("send_message_type","validation_result"), payload=decision)
        except Exception as exc:
            send_message(sender=AGENT_NAME, receiver=TARGET_RECEIVER, type="validation_error", payload={"ticket_id": msg.payload.get("ticket_id"), "error": str(exc)})

# helper to start loop in background thread
def start_langgraph_loop_in_thread():
    t = threading.Thread(target=langgraph_loop, daemon=True)
    t.start()
    return t
