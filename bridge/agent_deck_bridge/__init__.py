"""Agent Deck host bridge prototype."""

from .core import Session, SessionObservation, SessionRegistry
from .protocol import Envelope, MessageType, NormalizedState
from .runtime import BridgeRuntime

__all__ = [
    "BridgeRuntime",
    "Envelope",
    "MessageType",
    "NormalizedState",
    "Session",
    "SessionObservation",
    "SessionRegistry",
]

__version__ = "0.1.0"
