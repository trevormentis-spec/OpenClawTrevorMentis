"""Index assessment markdowns into a Chroma vector store for semantic retrieval.

Usage:
  python3 memory/index_memory.py                     # index all assessments
  python3 memory/index_memory.py --rebuild            # clear and re-index
"""
import sys, json
from pathlib import Path

# Resolve skill root: memory/ is one level below skill root
SKILL_ROOT = Path(__file__).resolve().parent.parent

ASSESS_DIR = SKILL_ROOT / 'assessments'
CHROMA_DIR = SKILL_ROOT / 'memory' / 'chroma_db'
INDEX_FILE = SKILL_ROOT / 'memory' / 'vector_index.json'

CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def get_embedding_fn():
    """Return a Chroma-compatible embedding function using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    from chromadb import Documents, EmbeddingFunction, Embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

    class EmbeddingFn(EmbeddingFunction):
        def __init__(self):
            pass

        def __call__(self, input: Documents) -> Embeddings:
            return model.encode(input, show_progress_bar=False).tolist()

    return EmbeddingFn()


def build_index(rebuild=False):
    """Build or update the Chroma collection from assessment markdowns."""
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if rebuild:
        try:
            client.delete_collection("daily_intel")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name="daily_intel",
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

    md_files = sorted(ASSESS_DIR.glob("*.md"))
    new_count = 0
    fallback_index = []

    for f in md_files:
        text = f.read_text(encoding="utf-8")
        doc_id = f.stem  # e.g. "europe"

        # Chunk by section (## headers)
        chunks = []
        current_section = "preamble"
        current_text = []

        for line in text.split("\n"):
            if line.startswith("## ") or line.startswith("# "):
                if current_text:
                    chunks.append((current_section, "\n".join(current_text).strip()))
                current_section = line.strip("# ").strip()
                current_text = [line]
            else:
                current_text.append(line)

        if current_text:
            chunks.append((current_section, "\n".join(current_text).strip()))

        # Add each chunk to Chroma
        for i, (section, chunk_text) in enumerate(chunks):
            chunk_id = f"{doc_id}_{i:03d}"
            if len(chunk_text) < 50:
                continue  # skip tiny fragments

            # Check if already exists
            existing = collection.get(ids=[chunk_id])
            if existing and existing["ids"]:
                continue  # already indexed

            collection.add(
                documents=[chunk_text],
                metadatas=[{
                    "file": f.name,
                    "section": section,
                    "theatre": doc_id,
                    "chunk_index": i,
                }],
                ids=[chunk_id],
            )
            new_count += 1

        # Also build the simple fallback index
        fallback_index.append({
            "file": f.name,
            "theatre": doc_id,
            "chars": len(text),
            "preview": text[:500],
        })

    # Save the simple index for SequenceMatcher fallback
    INDEX_FILE.write_text(json.dumps(fallback_index, indent=2), encoding="utf-8")

    count = collection.count()
    print(f"Chroma: {count} chunks across {len(md_files)} files ({new_count} new)")
    print(f"Fallback index: {len(fallback_index)} entries")


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    build_index(rebuild=rebuild)
