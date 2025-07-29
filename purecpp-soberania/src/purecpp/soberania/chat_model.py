# src/soberano_client/chat_model.py
from __future__ import annotations
from typing import Iterable, List, Optional
from .client import SoberanoClient
from .schemas import Message, ChatRequest, ChatResponse

class SoberanoChatModel:
    """
      - invoke(messages) -> string
      - stream(messages) -> generator[str]
      - batch(list_of_messages) -> list[str]
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "soberano-alpha",
        base_url: str = None,
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 20,
        presence_penalty: float = 1.5,
        max_tokens: int = 1000,
    ):
        self.client = SoberanoClient(api_key=api_key, base_url=base_url or "")
        self._default_params = dict(
            model=model,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            presence_penalty=presence_penalty,
            max_tokens=max_tokens,
        )

    def invoke(self, messages: List[Message]) -> str:
        req = ChatRequest(messages=messages, **self._default_params)
        resp: ChatResponse = self.client.chat(req)
        return resp.choices[0].message.content

    def stream(self, messages: List[Message]) -> Iterable[str]:
        req = ChatRequest(messages=messages, **self._default_params)
        for chunk in self.client.stream(req):
            yield chunk

    def batch(self, batches: List[List[Message]]) -> List[str]:
        outputs = []
        for msgs in batches:
            outputs.append(self.invoke(msgs))
        return outputs
