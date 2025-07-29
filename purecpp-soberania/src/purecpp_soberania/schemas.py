from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]

class Message(BaseModel):
    role: Role
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = Field(default="soberano-alpha")
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20
    presence_penalty: float = 1.5
    max_tokens: int = 1000
    stream: bool = False  # Optional streaming support

class ChoiceMessage(BaseModel):
    role: Role
    content: str

class Choice(BaseModel):
    index: int
    message: ChoiceMessage
    finish_reason: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
