import os
import sys
import fitz  # PyMuPDF
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# ── initialise embedding model ──────────────────────────────────────────────
print("Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)
print(f"Model loaded: {EMBED_MODEL}")

# ── initialise ChromaDB ──────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=CHROMA_PATH)

# delete existing collection if re-running
try:
    client.delete_collection("sakhibot_legal")
    print("Existing collection deleted — rebuilding fresh.")
except:
    pass

collection = client.create_collection(
    name="sakhibot_legal",
    metadata={"hnsw:space": "cosine"}
)
print("ChromaDB collection created.")

# ── helper: extract text from PDF ───────────────────────────────────────────
def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            full_text += f"\n[Page {page_num + 1}]\n{text}"
    doc.close()
    return full_text

# ── helper: split text into overlapping chunks ───────────────────────────────
def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 50:  # skip tiny chunks
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# ── process all PDFs ─────────────────────────────────────────────────────────
DOCS_PATH = "docs"

pdf_files = {
    "dv_act_2005.pdf":              "Domestic Violence Act 2005",
    "posh_act_2013.pdf":            "POSH Act 2013",
    "dowry_act.pdf":                "Dowry Prohibition Act",
    "maternity_act.pdf":            "Maternity Benefit Act",
    "equal_remuneration_act.pdf":   "Equal Remuneration Act",
    "ipc_498a.pdf":                 "Indian Penal Code",
    "crpc.pdf":                     "Code of Criminal Procedure",
    "constitution.pdf":             "Constitution of India",
    "hindu_marriage_act_1955.pdf":  "Hindu Marriage Act 1955"
}

total_chunks = 0
chunk_id = 0

for filename, doc_name in pdf_files.items():
    pdf_path = os.path.join(DOCS_PATH, filename)

    if not os.path.exists(pdf_path):
        print(f"SKIPPED (not found): {filename}")
        continue

    print(f"\nProcessing: {doc_name}...")

    # extract text
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        print(f"  WARNING: No text extracted from {filename} — may be scanned PDF")
        continue

    word_count = len(raw_text.split())
    print(f"  Extracted {word_count} words")

    # split into chunks
    chunks = split_into_chunks(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  Split into {len(chunks)} chunks")

    # embed and store in batches of 50
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        embeddings = model.encode(batch).tolist()

        ids = [f"chunk_{chunk_id + j}" for j in range(len(batch))]
        metadatas = [
            {
                "source": doc_name,
                "filename": filename,
                "chunk_index": i + j
            }
            for j in range(len(batch))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=batch,
            metadatas=metadatas
        )

        chunk_id += len(batch)

    total_chunks += len(chunks)
    print(f"  Stored {len(chunks)} chunks from {doc_name}")

print(f"\nIngestion complete. Total chunks stored: {total_chunks}")

# ── quick verification test ──────────────────────────────────────────────────
print("\nRunning 5 verification queries...")

test_queries = [
    "What is domestic violence and what protection does a woman have?",
    "How can a woman file a complaint against sexual harassment at workplace?",
    "What are the rights of a woman against dowry demands?",
    "What is maternity leave entitlement for working women in India?",
    "What are fundamental rights of women under the Constitution of India?",
]

for query in test_queries:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=2
    )
    top_source = results["metadatas"][0][0]["source"] if results["metadatas"][0] else "None"
    snippet = results["documents"][0][0][:80] if results["documents"][0] else "None"
    print(f"\nQ: {query[:60]}...")
    print(f"   Best match: {top_source}")
    print(f"   Snippet: {snippet}...")

print("\nDay 2 complete. ChromaDB is ready.")
