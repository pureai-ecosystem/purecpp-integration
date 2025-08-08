from __future__ import annotations

from .base import ICleaner
from ..exceptions import DependencyNotInstalled
from ..utils import normalize_whitespace

class ReadabilityCleaner(ICleaner):
    """
    Extracts the main body of the article and returns plain text/markdown.

    Requires:

    readability-lxml

    lxml
    """

    def __init__(self) -> None:
        try:
            from readability import Document  # type: ignore
            from lxml import html as lxml_html  # type: ignore
        except Exception as e:
            raise DependencyNotInstalled(
                "Install 'readability-lxml' and 'lxml' to use ReadabilityCleaner."
            ) from e
        self._Document = Document
        self._lxml_html = lxml_html

        try:
            from markdownify import markdownify as md_convert  # type: ignore
        except Exception:
            md_convert = None  # type: ignore
        self._md_convert = md_convert

    def to_markdown(self, html: str, mime: str) -> str:
        doc = self._Document(html)
        title = doc.short_title() or ""
        content_html = doc.summary(html_partial=True)

        root = self._lxml_html.fromstring(content_html)
        for bad in root.xpath("//script|//style|//noscript|//iframe|//svg"):
            bad.getparent().remove(bad)

        # Convert
        if self._md_convert is not None:
            md = self._md_convert(self._lxml_html.tostring(root, encoding="unicode"))
        else:
            md = root.text_content()

        if title and title not in md:
            md = f"# {title}\n\n{md}"

        return normalize_whitespace(md)
