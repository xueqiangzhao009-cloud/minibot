from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

class InboundMessage(BaseModel):
    session_id: str
    content: str
    channel: str = "cli"
    chat_id: Optional[str] = None
    sender_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    media: Optional[Dict[str, Any]] = None
    session_id_override: Optional[str] = None

class OutboundMessage(BaseModel):
    session_id: Optional[str] = None
    content: str = ""
    channel: str = "cli"
    chat_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

