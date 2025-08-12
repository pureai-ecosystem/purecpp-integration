from __future__ import annotations
from typing import Dict, List, Optional, Iterable, Tuple
from array import array
import uuid
import json
import os
import copy

import oracledb  # Recent versions have the `DB_TYPE_VECTOR` available.

from ..backend import VectorBackend
from ..document import Document
from ..types import QueryResult
from ..exceptions import (
    BackendClosed,
    DimensionMismatch,
    InsertionError,
    QueryError,
    InvalidConfiguration,
)
from ..registry import Registry


_METRIC_ALIASES = {
    "COSINE": "COSINE",
    "EUCLIDEAN": "EUCLIDEAN",     # L2
    "L2": "EUCLIDEAN",
    "L2_SQUARED": "L2_SQUARED",   # EUCLIDEAN_SQUARED
    "EUCLIDEAN_SQUARED": "L2_SQUARED",
    "DOT": "DOT",                 # -1*INNER_PRODUCT
    "MANHATTAN": "MANHATTAN",     # L1
    "L1": "MANHATTAN",
}

class OracleVectorBackend(VectorBackend):
    """
    Native backend for Oracle Database 23ai (AI Vector Search).

    Expected config:
    {
        "user": "ADMIN",
        "password": "******",
        "dsn": "MEUDB_high",                # tnsnames.ora alias (use the 23ai wallet one)
        "config_dir": "/path/to/wallet",
        "wallet_location": "/path/to/wallet",  # if necessary
        "wallet_password": "******",           # if necessary

        "table": "VDB_DOCS",
        "dim": 768,
        "metric": "COSINE",                   # see _METRIC_ALIASES
        "ensure_schema": True,

        # index (23ai)
        "index_algorithm": "HNSW",            # HNSW | IVF
        "index_params": "type HNSW, neighbors 40, efconstruction 500",
        "target_accuracy": 95,                # optional; 0<acc<=100

        # pool (optional)
        "pool_min": 1, "pool_max": 8, "pool_inc": 1,

        # session (optional)
        "target_schema": null,

        "debug": True
    }
    """

    def __init__(self, cfg: Dict):
        self.user: str = cfg["user"]
        self.password: str = cfg["password"]
        self.dsn: str = cfg["dsn"]
        self.config_dir: Optional[str] = cfg.get("config_dir")
        self.wallet_location: Optional[str] = cfg.get("wallet_location")
        self.wallet_password: Optional[str] = cfg.get("wallet_password")
        self.table: str = cfg.get("table", "VDB_DOCS")
        self.dim: int = int(cfg["dim"])
        raw_metric = str(cfg.get("metric", "COSINE")).upper()
        self.metric: str = _METRIC_ALIASES.get(raw_metric, raw_metric)
        self.ensure_schema: bool = bool(cfg.get("ensure_schema", True))
        self.target_schema: Optional[str] = cfg.get("target_schema")
        self.debug: bool = bool(cfg.get("debug", False))

        if self.metric not in _METRIC_ALIASES.values():
            raise InvalidConfiguration(
                f"Invalid metric: {raw_metric}. Use: {sorted(set(_METRIC_ALIASES.values()))}"
            )

        self.index_algorithm: str = str(cfg.get("index_algorithm", "HNSW")).upper()
        if self.index_algorithm not in {"HNSW", "IVF"}:
            raise InvalidConfiguration("`index_algorithm` must be either `HNSW` or `IVF`.")

        # index_params follows the new 23ai syntax, e.g.:
        # "type HNSW, neighbors 40, efconstruction 500"
        self.index_params: Optional[str] = cfg.get("index_params")
        self.target_accuracy: Optional[int] = cfg.get("target_accuracy", 95)

        #  Connection/Pool (with variations)
        if self.config_dir and not os.environ.get("TNS_ADMIN"):
            os.environ["TNS_ADMIN"] = self.config_dir

        base_kwargs = dict(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
            ssl_server_dn_match=True,
        )
        if self.config_dir:
            base_kwargs["config_dir"] = self.config_dir
        if self.wallet_location:
            base_kwargs["wallet_location"] = self.wallet_location
        if self.wallet_password:
            base_kwargs["wallet_password"] = self.wallet_password

        def _mask(d: Dict[str, object]) -> Dict[str, object]:
            return {k: ("***" if k in ("password", "wallet_password") else v)
                    for k, v in d.items()}

        def _try_connect_variants():
            variants = [copy.deepcopy(base_kwargs)]
            if "config_dir" in base_kwargs:
                v2 = copy.deepcopy(base_kwargs)
                v2.pop("config_dir", None)
                variants.append(v2)


            last_err = None
            for i, kw in enumerate(variants, 1):
                if self.debug:
                    print(f"[OracleBackend] connect attempt {i}: {_mask(kw)}")
                try:
                    return oracledb.connect(**kw)
                except oracledb.Error as e:
                    last_err = e
                    continue
            raise last_err

        use_pool = any(k in cfg for k in ("pool_min", "pool_max", "pool_inc"))
        if use_pool:
            try:
                if self.debug:
                    print(f"[OracleBackend] create_pool with {_mask(base_kwargs)}")
                self.pool = oracledb.create_pool(
                    min=cfg.get("pool_min", 1),
                    max=cfg.get("pool_max", 8),
                    increment=cfg.get("pool_inc", 1),
                    **base_kwargs,
                )
                self.conn = self.pool.acquire()
            except oracledb.Error:
                if self.debug:
                    print("[OracleBackend] pool failed, falling back to direct connect")
                self.pool = None
                self.conn = _try_connect_variants()
        else:
            self.pool = None
            self.conn = _try_connect_variants()

        if self.target_schema:
            with self.conn.cursor() as c:
                c.execute(f'ALTER SESSION SET CURRENT_SCHEMA = "{self.target_schema}"')

        self.dim = int(self.dim)

        if self.ensure_schema:
            self._ensure_schema()

    #  infra/DDL 

    def _ensure_schema(self) -> None:
        """
        Creates a VECTOR/JSON table and a vector index using the 23ai syntax:
          CREATE VECTOR INDEX ... ORGANIZATION {INMEMORY NEIGHBOR GRAPH|NEIGHBOR PARTITIONS}
        DISTANCE <metric> [WITH TARGET ACCURACY n] [PARAMETERS (...)]
        """
        cur = self.conn.cursor()

        # 0) Drop table to ensure index changes are applied
        drop_sql = f"""
        BEGIN
          EXECUTE IMMEDIATE 'DROP TABLE {self.table} PURGE';
        EXCEPTION WHEN OTHERS THEN
          IF SQLCODE != -942 THEN RAISE; END IF; -- ignore "table or view does not exist"
        END;"""
        cur.execute(drop_sql)

        # 1) Table with JSON and VECTOR
        table_sql_json = f"""
        BEGIN
          EXECUTE IMMEDIATE '
            CREATE TABLE {self.table} (
              id           VARCHAR2(64) PRIMARY KEY,
              page_content CLOB,
              metadata     JSON,
              embedding    VECTOR({self.dim})
            )
          ';
        EXCEPTION WHEN OTHERS THEN
          IF SQLCODE != -955 THEN RAISE; END IF;
        END;"""
        table_sql_clob = f"""
        BEGIN
          EXECUTE IMMEDIATE '
            CREATE TABLE {self.table} (
              id           VARCHAR2(64) PRIMARY KEY,
              page_content CLOB,
              metadata     CLOB CHECK (metadata IS JSON),
              embedding    VECTOR({self.dim})
            )
          ';
        EXCEPTION WHEN OTHERS THEN
          IF SQLCODE != -955 THEN RAISE; END IF;
        END;"""

        try:
            cur.execute(table_sql_json)
        except oracledb.DatabaseError:
            cur.execute(table_sql_clob)

        # 2) Vector Index — new syntax: CREATE VECTOR INDEX ...
        org = "INMEMORY NEIGHBOR GRAPH" if self.index_algorithm == "HNSW" else "NEIGHBOR PARTITIONS"
        acc_clause = ""
        if self.target_accuracy is not None:
            acc = int(self.target_accuracy)
            if not (0 < acc <= 100):
                raise InvalidConfiguration("target_accuracy deve estar em (0, 100]")
            acc_clause = f" WITH TARGET ACCURACY {acc}"
        params_clause = f" PARAMETERS ({self.index_params})" if self.index_params else ""

        vec_idx_sql = f"""
        BEGIN
          EXECUTE IMMEDIATE '
            CREATE VECTOR INDEX {self.table}_VEC_IDX
              ON {self.table}(embedding)
              ORGANIZATION {org}
              DISTANCE {self.metric}
              {acc_clause}{params_clause}
          ';
        EXCEPTION WHEN OTHERS THEN
          IF SQLCODE != -955 THEN RAISE; END IF;
        END;"""

        # Remove line breaks and double spaces caused by multiline strings
        vec_idx_sql = "\n".join(s.strip() for s in vec_idx_sql.splitlines())

        cur.execute(vec_idx_sql)

        #  3) JSON Search Index (optional, but helps with metadata filtering)
        jsi_sql = f"""
        BEGIN
          EXECUTE IMMEDIATE '
            CREATE SEARCH INDEX {self.table}_JSI
              ON {self.table}(metadata) FOR JSON
          ';
        EXCEPTION WHEN OTHERS THEN
          IF SQLCODE != -955 THEN RAISE; END IF;
        END;"""
        cur.execute(jsi_sql)

        self.conn.commit()

    #  helpers

    def _as_vec(self, emb: List[float]) -> array:
        if len(emb) != self.dim:
            raise DimensionMismatch(f"Expected dimension{self.dim}, Received={len(emb)}")
        return array("f", emb)  # FLOAT32 → DB_TYPE_VECTOR

    #  API VectorBackend 

    def is_open(self) -> bool:
        try:
            return self.conn is not None and self.conn.ping() is None
        except oracledb.Error:
            return False

    def insert(self, docs: Iterable[Document]) -> None:
        if not self.is_open():
            raise BackendClosed("Oracle backend closed")

        rows: List[Tuple[str, str, object, array]] = []
        for d in docs:
            doc_id = str(uuid.uuid4())
            rows.append((doc_id, d.page_content, d.metadata, self._as_vec(d.embedding)))

        cur = self.conn.cursor()
        try:
            # helps the driver bind JSON and VECTOR correctly
            cur.setinputsizes(None, None, oracledb.DB_TYPE_JSON, oracledb.DB_TYPE_VECTOR)
        except AttributeError:
            # Old driver versions: works without setinputsizes
            pass

        try:
            cur.executemany(
                f"INSERT INTO {self.table} (id, page_content, metadata, embedding) VALUES (:1, :2, :3, :4)",
                rows,
            )
            self.conn.commit()
        except oracledb.Error as e:
            raise InsertionError(str(e)) from e

    def query(
        self,
        embedding: List[float],
        k: int,
        filter: Optional[Dict[str, str]] = None,
    ) -> List[QueryResult]:
        if not self.is_open():
            raise BackendClosed("Oracle backend closed")

        cur = self.conn.cursor()

        # JSON filters (simple keys)
        where_clauses: List[str] = []
        binds: Dict[str, object] = {"vec": self._as_vec(embedding)}
        if filter:
            for i, (key, val) in enumerate(filter.items(), 1):
                b = f"v{i}"
                where_clauses.append(f"JSON_VALUE(metadata, '$.\"{key}\"') = :{b}")
                binds[b] = str(val)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # IMPORTANT:
        # - using the same metric as the index ensures index usage (approx) when possible
        # - do not bind FETCH FIRST
        sql = f"""
        SELECT
          id,
          page_content,
          metadata,
          VECTOR_DISTANCE(embedding, :vec, {self.metric}) AS score
        FROM {self.table}
        {where_sql}
        ORDER BY score
        FETCH FIRST {int(k)} ROWS ONLY
        """

        try:
            cur.execute(sql, binds)
            rows = cur.fetchall() or []
        except oracledb.Error as e:
            raise QueryError(str(e)) from e

        out: List[QueryResult] = []
        for (doc_id, page, metadata_obj, score) in rows:
            if not isinstance(metadata_obj, dict):
                try:
                    metadata_obj = json.loads(metadata_obj) if metadata_obj else {}
                except Exception:
                    metadata_obj = {}
            metadata_obj = {**metadata_obj, "id": doc_id}
            doc = Document(page_content=page, embedding=[], metadata=metadata_obj)
            out.append(QueryResult(doc=doc, score=float(score)))
        return out

    def close(self) -> None:
        try:
            if self.conn is not None:
                self.conn.close()
            if hasattr(self, "pool") and self.pool is not None:
                self.pool.close()
        finally:
            self.conn = None
            if hasattr(self, "pool"):
                self.pool = None


# Automatic registration
Registry.register_backend("oracle", lambda cfg: OracleVectorBackend(cfg))
