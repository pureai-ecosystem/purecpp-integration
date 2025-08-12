import os
import sys
from dotenv import load_dotenv
import oracledb

# Add the project directories to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'purecpp-huggingface-embedding')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'purecpp-oracledb')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'purecpp-websearch')))

from purecpp_huggingface_embedding.embedding import HuggingFaceEmbeddings
from purecpp_oracledb.vectordb.backends.oracle_backend import OracleVectorBackend
from purecpp_oracledb.vectordb.document import Document
from purecpp_websearch.websearch.pipeline import WebSearch
from purecpp_websearch.websearch.settings import Settings
load_dotenv()
def main():
    """Main function to run the RAG pipeline."""
    load_dotenv()

    # --- 1. Configuration ---
    # Brave Search API Key
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        raise ValueError("BRAVE_API_KEY environment variable not set.")

    # Oracle Database Configuration
    oracle_config = {
        "user": os.getenv("ORACLE_USER"),
        "password": os.getenv("ORACLE_PASSWORD"),
        "dsn": os.getenv("ORACLE_DSN"),
        "config_dir": os.getenv("ORACLE_CONFIG_DIR"),
        "wallet_location": os.getenv("ORACLE_WALLET_LOCATION"),
        "wallet_password": os.getenv("ORACLE_WALLET_PASSWORD"),
        "table": "rag_documents",
        "dim": 384,  # Based on the 'mini-lm' model
        "metric": "COSINE",
        "ensure_schema": True,
        "index_algorithm": "IVF",
    }
    if not all([oracle_config["user"], oracle_config["password"], oracle_config["dsn"]]):
        raise ValueError("Oracle database credentials (USER, PASSWORD, DSN) not fully set in environment.")

    # --- 2. Initialize Components ---
    print("Initializing components...")
    web_search_settings = Settings(brave_api_key=brave_api_key)
    web_search = WebSearch(settings=web_search_settings)
    embedding_model = HuggingFaceEmbeddings(model_name='mini-lm')
    vector_db = OracleVectorBackend(cfg=oracle_config)

    # --- 3. User Query ---
    user_query = "What are the latest advancements in AI?"
    print(f"\nUser Query: {user_query}")

    # --- 4. Web Search ---
    print("\nPerforming web search...")
    search_results = web_search.search_and_read(user_query, k=3)
    if not search_results:
        print("No web search results found.")
        return

    print(f"Found {len(search_results)} documents from the web.")

    # --- 5. Generate Embeddings and Prepare Documents ---
    print("\nGenerating embeddings for web documents...")
    documents_to_store = []
    for doc in search_results:
        embedding = embedding_model.embed_documents([doc.content])[0]
        documents_to_store.append(
            Document(page_content=doc.content, embedding=embedding, metadata={'url': doc.url, 'title': doc.title})
        )
    
    # --- 6. Store Data ---
    print("\nStoring documents in Oracle vector database...")
    vector_db.insert(documents_to_store)
    print("Documents stored successfully.")

    # --- 7. Query Embedding ---
    print("\nGenerating embedding for the user query...")
    query_embedding = embedding_model.embed_documents([user_query])[0]

    # --- 8. Retrieve Documents ---
    print("\nRetrieving relevant documents from the database...")
    retrieved_docs = vector_db.query(embedding=query_embedding, k=2)

    # --- 9. Final Output ---
    print("\n--- Top Retrieved Documents ---")
    for i, result in enumerate(retrieved_docs):
        print(f"\nDocument {i+1}:")
        print(f"  Title: {result.doc.metadata.get('title', 'N/A')}")
        print(f"  URL: {result.doc.metadata.get('url', 'N/A')}")
        print(f"  Score: {result.score}")
        print(f"  Content: {result.doc.page_content.read()[:500]}...")

    # --- 10. Cleanup ---
    vector_db.close()

if __name__ == "__main__":
    main()
