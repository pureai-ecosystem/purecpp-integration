from purecpp_oracledb.vectordb import make_backend, Document

CFG_DIR = ""                 
cfg = {
    "user": "",
    "password": "",
    "dsn": "",          
    "config_dir": CFG_DIR,
    "wallet_location": CFG_DIR,
    "wallet_password": "",       

    "table": "",               
    "dim": 4,                              
    "metric": "COSINE",                     
    "index_algorithm": "HNSW",               
    "index_params": "M 32 EF_CONSTRUCTION 200",
    "debug": True,
}

bk = make_backend("oracle", cfg)

# insert
bk.insert([
    Document("primeiro texto", [0.1,0.2,0.3,0.4], {"lang":"pt"}),
    Document("segundo texto",  [0.9,0.1,0.0,0.2], {"lang":"en"}),
])

# query
res = bk.query([0.1,0.2,0.25,0.35], k=2, filter={"lang": "pt"})
for r in res:
    print(f"score={r.score:.6f} meta={r.doc.metadata} page='{r.doc.page_content}'")

bk.close()
print("OK")
