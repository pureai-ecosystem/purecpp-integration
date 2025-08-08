from __future__ import annotations
import argparse
from .pipeline import WebSearch

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser("purecpp_websearch.websearch")
    p.add_argument("--provider", default="brave")
    p.add_argument("--cleaner", default="simple")
    p.add_argument("--q", dest="query", help="Query para busca")
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--mime", default="text/html")
    args = p.parse_args(argv)

    ws = WebSearch(provider=args.provider, cleaner=args.cleaner)
    if not args.query:
        p.error("--q é obrigatório")
    docs = ws.search_and_read(args.query, k=args.k, mime=args.mime)
    for i, d in enumerate(docs, 1):
        print(f"# [{i}] {d.title or d.url}\n\n{d.content}\n\n---\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
