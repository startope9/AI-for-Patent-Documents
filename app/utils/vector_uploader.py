# utils/vector_uploader.py
import os
import csv
import uuid
from typing import List, Dict
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# === CONFIGURATION ===
CHROMA_DB_DIR = os.path.join(os.path.dirname(
    __file__), "..", "chroma_db_patents")
COLLECTION_NAME = "patent_docs"

# === INITIALIZATION ===
print(f"🔧 Initializing ChromaDB client at: {CHROMA_DB_DIR}")
embedding_fn = DefaultEmbeddingFunction()

client = PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)
print(f"✅ Using collection: {COLLECTION_NAME}")


def load_csv_to_vectordb(csv_path: str) -> int:
    """
    Load documents from a parsed patent CSV into ChromaDB.
    Returns the number of documents added.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📄 Loading CSV: {csv_path}")
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = str(uuid.uuid4())
            document_text = "\n\n".join([
                f"PID: {row.get('pid', '')}",
                f"Abstract: {row.get('Abstract', '')}",
                f"Claims: {row.get('Claims', '')}",
                f"Description: {row.get('Description', '')}"
            ])

            collection.add(
                documents=[document_text],
                metadatas=[{"pid": row.get("pid", "")}],
                ids=[doc_id]
            )
            count += 1

            if count % 10 == 0:
                print(f"📝 Inserted {count} documents...")

    print(
        f"🎉 Finished inserting {count} documents into collection '{COLLECTION_NAME}'")
    return count
