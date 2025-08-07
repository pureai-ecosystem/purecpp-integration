import oracledb

CFG_DIR = ""
USER = ""
PWD  = ""
DSN  = ""

TABLE = "VDB_DOCS_VEC23"
IDX   = f"{TABLE}_VEC_IDX"

conn = oracledb.connect(
    user=USER, password=PWD, dsn=DSN,
    config_dir=CFG_DIR, wallet_location=CFG_DIR, wallet_password=PWD
)
cur = conn.cursor()

print("Current indexes:")
cur.execute("""
    SELECT index_name, index_type, status
    FROM user_indexes
    WHERE table_name = :t
""", {"t": TABLE.upper()})
for row in cur.fetchall():
    print("  ", row)

try:
    print(f"Drop {IDX} ...")
    cur.execute(f"DROP INDEX {IDX}")
    conn.commit()
    print("OK: index ")
except oracledb.DatabaseError as e:
    if "ORA-01418" in str(e):
        print("Index não existia, seguindo...")
    else:
        raise

sql_create = f"""
CREATE VECTOR INDEX {IDX}
  ON {TABLE}(embedding)
  ORGANIZATION NEIGHBOR PARTITIONS
  DISTANCE COSINE
  WITH TARGET ACCURACY 95
  PARAMETERS (type IVF, neighbor partitions 256)
"""
print("Creating IVF...")
cur.execute(sql_create)
conn.commit()
print("OK: IVF created.")

cur.close()
conn.close()
print("Completed.")
