from __future__ import annotations
from abc import ABC, abstractmethod

class ICleaner(ABC):
    """Equivalent interface to the C++ header:
       virtual std::string to_markdown(const std::string& html,
                                       const std::string& mime) = 0;
    """

    @abstractmethod
    def to_markdown(self, html: str, mime: str) -> str:
        """Converte conteúdo (HTML/texto) para Markdown."""
        raise NotImplementedError
