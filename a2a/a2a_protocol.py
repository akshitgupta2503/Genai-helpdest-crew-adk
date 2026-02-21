# a2a/a2a_protocol.py

import threading
import queue
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ------------------------------------------
# MESSAGE ENVELOPE (Pydantic Structured)
# ------------------------------------------
class A2AMessage(BaseModel):
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ------------------------------------------
# AGENT-TO-AGENT MESSAGE BUS
# ------------------------------------------
class A2ABus:
    def __init__(self):
        self.queues: Dict[str, "queue.Queue[A2AMessage]"] = {}
        self.lock = threading.Lock()

    # Register agent to bus
    def register(self, agent_name: str):
        with self.lock:
            if agent_name not in self.queues:
                self.queues[agent_name] = queue.Queue()
        return True

    # Send message to agent
    def send(self, message: A2AMessage):
        if message.receiver not in self.queues:
            raise Exception(f"A2A Error: Receiver agent '{message.receiver}' not registered.")
        self.queues[message.receiver].put(message)

    # Receive message (blocking or non-blocking)
    def receive(self, agent_name: str, timeout: Optional[float] = None) -> Optional[A2AMessage]:
        if agent_name not in self.queues:
            raise Exception(f"A2A Error: Agent '{agent_name}' not registered.")

        try:
            return self.queues[agent_name].get(timeout=timeout)
        except queue.Empty:
            return None


# GLOBAL BUS INSTANCE
BUS = A2ABus()


# ------------------------------------------
# Helper function for agents to send messages
# ------------------------------------------
def send_message(sender: str, receiver: str, type: str, payload: Dict[str, Any]):
    msg = A2AMessage(
        sender=sender,
        receiver=receiver,
        type=type,
        payload=payload
    )
    BUS.send(msg)
    return msg
