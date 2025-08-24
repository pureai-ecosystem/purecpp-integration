from __future__ import annotations
from typing import Dict, List, Optional, Iterable, Tuple
import json, uuid
import oracledb
import numpy as np

from ..backend import VectorBackend
from ..document import Document
from ..types import QueryResult
from ..exceptions import BackendClosed, DimensionMismatch, InsertionError, QueryError, InvalidConfiguration
from ..registry import Registry
from ..utils import pack_f32, unpack_f32, cosine_distance

class RDSOracleVectorBackend(VectorBackend):
    """Vector backend for **AWS RDS Oracle (19c/21c)**.
Stores embeddings as BLOBs (float32) and ranks by cosine similarity in the app.


    cfg esperado:
    {
      "user": "admin",
      "password": "...",
      "host": "rds-...amazonaws.com",
      "port": 1521,
      "service_name": "ORCL",      
      "table": "VDB_DOCS",
      "dim": 768,
      "ensure_schema": True,
      "candidate_limit": 3000,       
      "debug": False
    }
    """

    def __init__(self, cfg: Dict):
        self.user = cfg["user"]
        self.password = cfg["password"]
        self.host = cfg["host"]
        self.port = int(cfg.get("port", 1521))
        self.service_name = cfg.get("service_name")
        self.table = cfg.get("table", "VDB_DOCS")
        self.dim = int(cfg["dim"])
        self.ensure_schema = bool(cfg.get("ensure_schema", True))
        self.candidate_limit = int(cfg.get("candidate_limit", 2000))
        self.debug = bool(cfg.get("debug", False))

        if not self.service_name:
            raise InvalidConfiguration("Define `'service_name'` to connect to the Oracle RDS.")

        dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
        self.conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)

        if self.ensure_schema:
            self._ensure_schema()

    # ---------- DDL ----------
    def _ensure_schema(self) -> None:
        stmts = [
            f"""
            BEGIN
              EXECUTE IMMEDIATE 'CREATE TABLE {self.table} (
                id           VARCHAR2(64) PRIMARY KEY,
                page_content CLOB,
                metadata     CLOB CHECK (metadata IS JSON),
                embedding    BLOB,
                dim          NUMBER(4) NOT NULL,
                l2norm       BINARY_DOUBLE
              )';
            EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF; END;""",
            f"""
            BEGIN
              EXECUTE IMMEDIATE 'CREATE SEARCH INDEX {self.table}_JSI ON {self.table}(metadata) FOR JSON';
            EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN NULL; END IF; END;""",  
        ]
        with self.conn.cursor() as c:
            for s in stmts:
                c.execute(s)
        self.conn.commit()

    def is_open(self) -> bool:
        try:
            return self.conn is not None and self.conn.ping() is None
        except oracledb.Error:
            return False

    def insert(self, docs: Iterable[Document]) -> None:
        if not self.is_open():
            raise BackendClosed("closed connection")
        rows: List[Tuple[str, str, str, bytes, int, float]] = []
        for d in docs:
            if len(d.embedding) != self.dim:
                raise DimensionMismatch(f"expected dim={self.dim}, received={len(d.embedding)}")
            doc_id = str(uuid.uuid4())
            buf = pack_f32(d.embedding)
            l2 = float(np.linalg.norm(d.embedding))
            rows.append((doc_id, d.page_content, json.dumps(d.metadata or {}), buf, self.dim, l2))
        sql = f"INSERT INTO {self.table} (id, page_content, metadata, embedding, dim, l2norm) VALUES (:1,:2,:3,:4,:5,:6)"
        try:
            with self.conn.cursor() as c:
                c.executemany(sql, rows)
            self.conn.commit()
        except oracledb.Error as e:
            raise InsertionError(str(e)) from e

    def query(self, embedding: List[float], k: int, filter: Optional[Dict[str,str]] = None) -> List[QueryResult]:
        if not self.is_open():
            raise BackendClosed("closed connection")
        if len(embedding) != self.dim:
            raise DimensionMismatch(f"expected dim={self.dim}, **received**={len(embedding)}")

        where = ["dim = :dim"]
        binds: Dict[str, object] = {"dim": self.dim}
        if filter:
            for i, (key, val) in enumerate(filter.items(), 1):
                if val is None:
                    continue
                b = f"b{i}"  
                where.append(f"JSON_VALUE(metadata, '$.\"{key}\"') = :{b}")
                binds[b] = str(val)

        where_sql = "WHERE " + " AND ".join(where)

        limit = max(self.candidate_limit, int(k))
        sql = f"""
            SELECT id, page_content, metadata, embedding
            FROM {self.table}
            {where_sql}
            FETCH FIRST {limit} ROWS ONLY
        """

        if self.debug:
            print("[RDSOracleVectorBackend] SQL:\n", sql)
            print("[RDSOracleVectorBackend] BINDS:", binds)

        try:
            with self.conn.cursor() as c:
                c.execute(sql, binds)
                rows = c.fetchall() or []
        except oracledb.Error as e:
            raise QueryError(str(e)) from e

        q = np.asarray(embedding, dtype=np.float32)
        scored: List[Tuple[float, str, object, object]] = []

        for (doc_id, page, meta, emb_lob) in rows:
            emb_bytes = emb_lob.read() if hasattr(emb_lob, "read") else emb_lob
            a = unpack_f32(emb_bytes)
            dist = cosine_distance(a, q)

            # page_content (CLOB) -> str
            page_text = page.read() if hasattr(page, "read") else page

            # metadata (CLOB) -> str -> dict
            meta_text = meta.read() if hasattr(meta, "read") else meta
            scored.append((dist, doc_id, page_text, meta_text))

        scored.sort(key=lambda x: x[0])

        out: List[QueryResult] = []
        for dist, doc_id, page_text, meta_text in scored[:k]:
            md = {}
            if isinstance(meta_text, (bytes, bytearray)):
                try:
                    meta_text = meta_text.decode("utf-8", errors="ignore")
                except Exception:
                    meta_text = ""
            if isinstance(meta_text, str) and meta_text:
                try:
                    md = json.loads(meta_text)
                except Exception:
                    md = {}
            md["id"] = doc_id
            out.append(QueryResult(doc=Document(page_text, [], md), score=float(dist)))
        return out




    def close(self) -> None:
        try:
            if self.conn: self.conn.close()
        finally:
            self.conn = None

Registry.register_backend("oracle_rds", lambda cfg: RDSOracleVectorBackend(cfg))