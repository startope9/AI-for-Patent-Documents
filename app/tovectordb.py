import os
import csv
import uuid
import sys
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# Fix field size limit for large patent data (Windows-safe)
csv.field_size_limit(10_000_000)

CSV_PATH = "parsed_patents/coffee_50patents.csv"
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db_patents")
COLLECTION_NAME = "patent_docs"

client = PersistentClient(path=CHROMA_DB_DIR)
embedding_fn = DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)

with open(CSV_PATH, "r", encoding="utf-8") as f:
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

print(
    f"✅ Successfully inserted documents into ChromaDB at '{CHROMA_DB_DIR}' in collection '{COLLECTION_NAME}'.")
