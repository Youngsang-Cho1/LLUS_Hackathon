import json
import os
import chromadb
from chromadb.utils import embedding_functions

# Use the best performing small embedding model (BGE)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

def ingest_courses_to_chroma():
    print("🚀 Initializing ChromaDB and Embedding Model...")
    
    # Create a persistent ChromaDB instance in the backend directory
    db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Initialize the high-performance embedding function
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    
    # Get or create the collection
    collection_name = "nyu_courses"
    print(f"📁 Getting or creating collection '{collection_name}'...")
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )
    
    # Load the scraped data
    json_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "course_descriptions.json")
    print(f"📖 Loading course data from {json_path}...")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            course_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {json_path} not found. Please ensure the scraper has run.")
        return

    ids = []
    documents = []
    metadatas = []
    
    print(f"⚙️ Processing {len(course_data)} courses...")
    
    for course_code, info in course_data.items():
        title = info.get("title", "")
        description = info.get("description", "")
        
        # Skip courses without descriptions or meaningful content
        if not description or description.strip() == "":
            continue
            
        # The document is what gets embedded. We combine title + description for rich context.
        document_text = f"{title}\n{description}"
        
        # Metadata allows for filtering (e.g. only show CS classes)
        metadata = {
            "course_code": course_code,
            "title": title,
            "subject_prefix": info.get("subject_prefix", "")
        }
        
        ids.append(course_code)
        documents.append(document_text)
        metadatas.append(metadata)
        
    print(f"🧠 Generating embeddings and inserting {len(documents)} courses into ChromaDB...")
    print("   (This might take a few minutes on the first run as it downloads the model...)")
    
    # Upsert into Chroma (batch size of 100 for safety)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        
        collection.upsert(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        print(f"   ... upserted batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
        
    print("✅ Indexing Complete! Your courses are now semantically searchable.")

if __name__ == "__main__":
    ingest_courses_to_chroma()
