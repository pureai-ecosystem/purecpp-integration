from __future__ import annotations
import argparse, json, os, glob
from typing import List, Dict
from tqdm import tqdm

from rds_vdb.registry import Registry
from rds_vdb.document import Document
from rds_vdb.embedder.dummy import DummyEmbedder



def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def chunk(text: str, size: int, overlap: int) -> List[str]:
    if size <= 0: return [text]
    out = []
    i = 0
    while i < len(text):
        out.append(text[i:i+size])
        i += max(1, size-overlap)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ingest text files into the VDB (RDS Oracle)")
    ap.add_argument("folder", help="pasta com .txt/.md")
    ap.add_argument("--dim", type=int, default=768)
    ap.add_argument("--pattern", default="**/*.txt,**/*.md")
    ap.add_argument("--chunk", type=int, default=800)
    ap.add_argument("--overlap", type=int, default=100)
    ap.add_argument("--metadata", default="{}", help='JSON ex: {"lang":"pt"}')

    ap.add_argument("--host", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--service_name", required=True)
    ap.add_argument("--table", default="VDB_DOCS")
    ap.add_argument("--candidate_limit", type=int, default=3000)
    args = ap.parse_args()

    cfg = {
        "user": args.user,
        "password": args.password,
        "host": args.host,
        "service_name": args.service_name,
        "table": args.table,
        "dim": args.dim,
        "ensure_schema": True,
        "candidate_limit": args.candidate_limit,
    }
    bk = Registry.make("oracle_rds", cfg)
    embedder = DummyEmbedder(dim=args.dim)

    meta_base: Dict[str, str] = json.loads(args.metadata)

    patterns = [p.strip() for p in args.pattern.split(",")]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(args.folder, p), recursive=True))
    files = sorted(set(files))

    for path in tqdm(files, desc="ingest"):
        text = read_text_file(path)
        parts = chunk(text, args.chunk, args.overlap)
        vecs = embedder.embed(parts)
        docs = []
        for part, vec in zip(parts, vecs):
            md = dict(meta_base)
            md.update({"source": os.path.relpath(path, args.folder)})
            docs.append(Document(page_content=part, embedding=vec, metadata=md))
        if docs:
            bk.insert(docs)

    bk.close()