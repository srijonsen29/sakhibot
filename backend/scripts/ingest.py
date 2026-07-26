import sys
import os
from pathlib import Path

# Allow `python scripts/ingest.py` from backend/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from app.config import QDRANT_URL, QDRANT_API_KEY, EMBED_MODEL

print("Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

if client.collection_exists(collection_name="sakhibot_legal"):
    client.delete_collection(collection_name="sakhibot_legal")
    print("Old collection deleted.")

client.create_collection(
    collection_name="sakhibot_legal",
    vectors_config=VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
)

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    pages_ok = 0
    total_pages = len(doc)          # ← get length BEFORE closing
    for i, page in enumerate(doc):
        t = page.get_text().strip()
        if len(t) > 20:
            text += f"\n[Page {i+1}]\n{t}"
            pages_ok += 1
    doc.close()
    return text, pages_ok, total_pages   # ← return saved value

def chunk_text(text, size, overlap):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        if len(chunk.strip()) > 30:
            chunks.append(chunk)
        i += size - overlap
    return chunks

# ── chunk size per document ───────────────────────────────────────────────────
# short acts use 150 words so each section becomes its own chunk
# long acts capped to keep DB balanced
CONFIGS = {
    "dv_act_2005.pdf": {
        "name": "Domestic Violence Act 2005",
        "size": 150, "overlap": 30, "cap": None
    },
    "posh_act_2013.pdf": {
        "name": "POSH Act 2013",
        "size": 150, "overlap": 30, "cap": None
    },
    "dowry_act.pdf": {
        "name": "Dowry Prohibition Act",
        "size": 100, "overlap": 20, "cap": None
    },
    "maternity_act.pdf": {
        "name": "Maternity Benefit Act",
        "size": 150, "overlap": 30, "cap": None
    },
    "equal_remuneration_act.pdf": {
        "name": "Equal Remuneration Act",
        "size": 100, "overlap": 20, "cap": None
    },
    "ipc_498a.pdf": {
        "name": "Indian Penal Code",
        "size": 200, "overlap": 40, "cap": 100
    },
    "crpc.pdf": {
        "name": "Code of Criminal Procedure",
        "size": 250, "overlap": 50, "cap": 80
    },
    "constitution.pdf": {
        "name": "Constitution of India",
        "size": 250, "overlap": 50, "cap": 60
    },
}

DOCS = str(Path(__file__).resolve().parent.parent / "data" / "legal_docs")
chunk_id = 0
total = 0
summary = []

for filename, cfg in CONFIGS.items():
    path = os.path.join(DOCS, filename)
    if not os.path.exists(path):
        print(f"NOT FOUND: {filename}")
        summary.append((cfg["name"], 0, "[FAIL] FILE NOT FOUND"))
        continue

    text, pages_ok, pages_total = extract_text(path)
    coverage = pages_ok / pages_total * 100 if pages_total else 0

    if not text.strip() or pages_ok < 2:
        print(f"[WARN] {filename}: only {pages_ok}/{pages_total} pages have text -- scanned PDF!")
        summary.append((cfg["name"], 0, "[FAIL] SCANNED -- re-download needed"))
        continue

    words = len(text.split())
    chunks = chunk_text(text, cfg["size"], cfg["overlap"])

    if cfg["cap"]:
        chunks = chunks[:cfg["cap"]]

    print(f"\n{cfg['name']}")
    print(f"  Pages: {pages_ok}/{pages_total} | Words: {words} | "
          f"Chunks: {len(chunks)} (size={cfg['size']})")

    for i in range(0, len(chunks), 50):
        batch = chunks[i:i+50]
        emb = model.encode(batch).tolist()
        
        points = []
        for j in range(len(batch)):
            payload = {
                "source": cfg["name"],
                "filename": filename,
                "chunk_index": i+j,
                "document": batch[j]
            }
            points.append(PointStruct(id=chunk_id+j, vector=emb[j], payload=payload))
        
        client.upsert(
            collection_name="sakhibot_legal",
            points=points
        )
        chunk_id += len(batch)

    total += len(chunks)
    summary.append((cfg["name"], len(chunks), "[OK]"))

# ── summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"Total chunks: {total}")
print(f"{'='*55}")
print(f"{'Document':<35} {'Chunks':>6}  Status")
print("-"*55)
for name, count, status in summary:
    bar = "|" * min(count // 2, 25)
    print(f"{name:<35} {count:>6}  {status} {bar}")

# ── DV Act check ──────────────────────────────────────────────────────────────
dv = next((c for n, c, _ in summary if "Domestic Violence" in n), 0)
if dv == 0:
    print("\n[FAIL] CRITICAL: DV Act still 0 chunks!")
    print("   Your file is probably named wrong.")
    print("   Run: ls docs/ and check the exact filename.")
    print("   It must be exactly: dv_act_2005.pdf")
else:
    print(f"\n[OK] DV Act has {dv} chunks -- good!")