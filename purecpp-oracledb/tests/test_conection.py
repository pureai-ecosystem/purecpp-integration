import oracledb

CFG_DIR = ""

conn = oracledb.connect(
    user="",
    password="",
    dsn="",
    config_dir=CFG_DIR,
    wallet_location=CFG_DIR,        
    wallet_password="", 
)
with conn.cursor() as c:
    c.execute("select sysdate from dual")
    print(c.fetchone())
conn.close()
