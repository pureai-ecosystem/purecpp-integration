from __future__ import annotations
from typing import Optional

from ..exceptions import UnsupportedMimeError, DependencyNotInstalled
from ..mimes import Mime
from ..utils import normalize_whitespace
from .base import ICleaner

try:
    from markdownify import markdownify as md_convert  # type: ignore
except Exception:
    md_convert = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception as e:
    BeautifulSoup = None  # type: ignore
    _bs4_error: Optional[Exception] = e
else:
    _bs4_error = None


class SimpleCleaner(ICleaner):
    """
    **Basic converter:**
    * **For HTML/XHTML/XML:** Cleans up noisy tags and converts to Markdown (`markdownify` if available; otherwise, it returns plain text).
    * **For TEXT/PLAIN:** Normalizes whitespace and returns the text.
    """

    def to_markdown(self, html: str, mime: str) -> str:
        m = Mime.from_string(mime)
        if m is None:
            # fallback 
            treat_as_html = "<" in html and ">" in html
        else:
            treat_as_html = m in {
                Mime.TEXT_HTML,
                Mime.APPLICATION_XHTML,
                Mime.APPLICATION_XML,
            }

        if treat_as_html:
            if BeautifulSoup is None:
                raise DependencyNotInstalled(
                    f"BeautifulSoup (bs4) not installed: {_bs4_error}"
                )

            soup = BeautifulSoup(html, "html.parser")

            for tag in soup(["script", "style", "noscript", "iframe", "template", "svg"]):
                tag.decompose()

            for el in soup(True):
                for attr in ("style", "class", "onclick", "onload"):
                    if attr in el.attrs:
                        del el.attrs[attr]

            if md_convert is not None:
                md = md_convert(str(soup))
            else:
                md = soup.get_text("\n")

            return normalize_whitespace(md)

        if m is None or m == Mime.TEXT_PLAIN:
            return normalize_whitespace(html)

        raise UnsupportedMimeError(f"MIME type not supported: {mime}")
