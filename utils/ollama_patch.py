# utils/ollama_patch.py

from crewai import Agent
from utils.ollama_client import OllamaClient

ollama = OllamaClient(model="gemma:2b")

def patched_run(self, prompt: str, **kwargs):
    return ollama.run(prompt)

# Monkey-patch globally
Agent.run = patched_run
