# mcp_server/mcp_server.py
"""
Real MCP-style Tool Server using FastAPI.
Agents (CrewAI / ADK / LangGraph) will call these tools through HTTP.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import sqlite3
from pathlib import Path

app = FastAPI(title="MCP Tool Server", version="1.0")

# Path to the SQLite KB created in Step 1
DATA_FOLDER = Path("data")
DB_FILE = DATA_FOLDER / "sample_kb.sqlite"


# ------------------------------
# Generic ToolCall Input Model
# ------------------------------
class ToolCall(BaseModel):
    tool_name: str
    payload: Dict[str, Any]


# ------------------------------
# SQLite KB Lookup Tool
# ------------------------------
def run_sqlite_keyword_search(query: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, content FROM kb WHERE title LIKE ? LIMIT 5",
        (f"%{query}%",),
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"title": r[0], "content": r[1]} for r in rows]


# ------------------------------
# File Parser Tool
# ------------------------------
def run_file_parser(path: str):
    path = Path(path)
    if not path.exists():
        return {"error": "File not found"}

    text = path.read_text(encoding="utf-8")
    return {"text": text[:3000]}  # limit output for safety


# ------------------------------
# Web Search Tool (Mock for Now)
# ------------------------------
def run_web_search(query: str):
    return {
        "snippets": [
            f"Mock snippet for '{query}' - replace with live search later.",
            f"Search result about '{query}' from simulated engine."
        ]
    }


# ------------------------------
# MCP Tool Dispatcher Endpoint
# ------------------------------
@app.post("/call_tool")
async def call_tool(request: ToolCall):
    """Dispatch incoming tool calls to the correct handler."""
    tool = request.tool_name
    payload = request.payload

    if tool == "sqlite_lookup":
        q = payload.get("query", "")
        return {"hits": run_sqlite_keyword_search(q)}

    elif tool == "file_parser":
        path = payload.get("path", "")
        return run_file_parser(path)

    elif tool == "web_search":
        q = payload.get("query", "")
        return run_web_search(q)

    else:
        return {"error": f"Unknown tool: {tool}"}


# ------------------------------
# MCP SERVER ENTRY POINT
# ------------------------------
if __name__ == "__main__":
    print("🔥 MCP Tool Server Running on: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
