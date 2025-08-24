from __future__ import annotations
import argparse, json
from rds_vdb.registry import Registry
from rds_vdb.embedder.dummy import DummyEmbedder

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Similarity search (cosine) on the Oracle RDS VDB")
    ap.add_argument("text")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--filter", default="{}", help='JSON ex: {"lang":"pt"}')
    ap.add_argument("--dim", type=int, default=768)

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
        "ensure_schema": False,
        "candidate_limit": args.candidate_limit,
    }
    bk = Registry.make("oracle_rds", cfg)
    embedder = DummyEmbedder(dim=args.dim)

    qvec = embedder.embed([args.text])[0]
    flt = json.loads(args.filter)
    results = bk.query(qvec, k=args.k, filter=flt)

    for i, r in enumerate(results, 1):
        print(f"#{i} score={r.score:.6f} id={r.doc.metadata.get('id')} meta={r.doc.metadata}")
        print(r.doc.page_content[:240].replace("\n"," ") + ("..." if len(r.doc.page_content)>240 else ""))
        print("-")

    bk.close()