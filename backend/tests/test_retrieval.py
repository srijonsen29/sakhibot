import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, EMBED_MODEL, TOP_K

model = SentenceTransformer(EMBED_MODEL)
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection("sakhibot_legal")

print(f"Total chunks in DB: {collection.count()}")
print("Type your query (or 'quit' to exit)\n")

while True:
    query = input("Query: ").strip()
    if query.lower() == "quit":
        break
    if not query:
        continue

    embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=TOP_K
    )

    print(f"\nTop {TOP_K} results:\n")
    for i, (doc, meta) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        print(f"  [{i+1}] Source: {meta['source']}")
        print(f"       {doc[:150]}...")
        print()