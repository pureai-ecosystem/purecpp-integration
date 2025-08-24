from __future__ import annotations
import argparse, os, oracledb

parser = argparse.ArgumentParser(description="Create/validate schema for VDB on Oracle RDS")
parser.add_argument("--host", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--service_name", required=True)
parser.add_argument("--port", type=int, default=1521)
parser.add_argument("--table", default="VDB_DOCS")
args = parser.parse_args()

conn = oracledb.connect(user=args.user, password=args.password,
                        dsn=oracledb.makedsn(args.host, args.port, service_name=args.service_name))
with conn.cursor() as c:
    for s in [
        f"""
        BEGIN
          EXECUTE IMMEDIATE 'CREATE TABLE {args.table} (
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
          EXECUTE IMMEDIATE 'CREATE SEARCH INDEX {args.table}_JSI ON {args.table}(metadata) FOR JSON';
        EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN NULL; END IF; END;""",
    ]:
        c.execute(s)
conn.commit(); conn.close()
print("Schema ok.")