# crew/knowledge_agent.py
# Knowledge agent: synthesize KB + web + ADK context into troubleshooting steps

import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/knowledge_agent.yaml"))

knowledge_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    verbose=True
)


def knowledge_loop():
    BUS.register("knowledge_agent")
    while True:
        msg = BUS.receive("knowledge_agent", timeout=1)
        if not msg:
            continue

        try:
            payload = msg.payload
            ticket_id = payload.get("ticket_id")

            kb_hits = payload.get("kb_hits", [])
            web_snippets = payload.get("web_snippets", [])
            # ADK enriched context may arrive as text or dict
            enriched = payload.get("enriched_context")
            enriched_parsed = enriched if isinstance(enriched, dict) else safe_json_parse(enriched) if enriched else {}

            prompt = (
                "You are a senior support analyst. Based on the following inputs, "
                "create a JSON array of clear step-by-step troubleshooting instructions.\n\n"
                f"KB HITS: {kb_hits}\n\nWEB SNIPPETS: {web_snippets}\n\nADK CONTEXT: {enriched_parsed}\n\n"
                "Return only a JSON array like: [\"step1\",\"step2\", ...]"
            )

            raw_steps = knowledge_agent.run(prompt)
            steps = safe_json_parse(raw_steps)

            send_message(
                sender="knowledge_agent",
                receiver="troubleshoot_agent",
                type="steps_ready",
                payload={"ticket_id": ticket_id, "steps": steps}
            )
        except Exception as e:
            send_message(
                sender="knowledge_agent",
                receiver="monitor_agent",
                type="agent_error",
                payload={"agent": "knowledge_agent", "error": str(e), "ticket_id": payload.get("ticket_id")}
            )
