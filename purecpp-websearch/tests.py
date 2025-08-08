import os
import sys
import re

def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:80] or "sem-titulo"

def main() -> int:
    if not os.getenv("BRAVE_API_KEY"):
        print("ERRO: defina BRAVE_API_KEY (ex.: export BRAVE_API_KEY='seu_token')")
        return 1

    from purecpp_websearch.websearch import WebSearch

    ws = WebSearch(provider="brave", cleaner="simple")

    # 1) Busca
    results = ws.search(
        "quantization low rank",
        k=5,
        lang="en",
        ui_lang="en-US",
        country="US",
        freshness="pm",
    )
    print("\n[SEARCH] Top resultados:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.title or '(sem título)'} -> {r.url}")

    # 2) Busca + leitura
    print("\n[READ] Baixando e limpando top 3 docs...")
    docs = ws.search_and_read(
        "retrieval augmented generation faiss",
        k=3,
        mime="text/html",
        lang="en",
        ui_lang="en-US",
        country="US",
        freshness="pm",
    )

    # 3) PRINTAR o Markdown e salvar em arquivos .md
    for i, d in enumerate(docs, 1):
        title = (d.title or d.url or "").strip()
        fname = f"doc_{i}_{slugify(title)}.md"

        print(f"\n# [{i}] {title}\n")
        print(d.content)  # <<< imprime o MARKDOWN completo no console
        print("\n" + "-" * 80 + "\n")

        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(d.content)

        print(f"[salvo] {fname} ({len(d.content)} chars markdown)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
