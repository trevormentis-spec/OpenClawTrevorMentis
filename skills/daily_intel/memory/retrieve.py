"""Retrieve top-k relevant chunks from Chroma vector memory.

Usage:
  python3 memory/retrieve.py <query>
  python3 memory/retrieve.py <query> --top-k 5
"""
import sys, json
from pathlib import Path
from difflib import SequenceMatcher

SKILL_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = SKILL_ROOT / 'memory' / 'chroma_db'
INDEX_FILE = SKILL_ROOT / 'memory' / 'vector_index.json'


def get_embedding_fn():
    """Same embedding function as index_memory.py"""
    from sentence_transformers import SentenceTransformer
    from chromadb import Documents, EmbeddingFunction, Embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

    class EmbeddingFn(EmbeddingFunction):
        def __init__(self):
            pass

        def __call__(self, input: Documents) -> Embeddings:
            return model.encode(input, show_progress_bar=False).tolist()

    return EmbeddingFn()


def retrieve(query: str, top_k: int = 3):
    """Try Chroma first, fall back to SequenceMatcher on flat index."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(
            name="daily_intel",
            embedding_function=get_embedding_fn(),
        )

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        docs = []
        for i in range(len(results["ids"][0])):
            docs.append({
                "chunk_id": results["ids"][0][i],
                "content": results["documents"][0][i][:500],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return docs

    except Exception as e:
        # Chroma not available or not built — use SequenceMatcher fallback
        if INDEX_FILE.exists():
            data = json.loads(INDEX_FILE.read_text())
            scored = []
            for item in data:
                score = SequenceMatcher(
                    None, query.lower(), item["preview"].lower()
                ).ratio()
                scored.append((score, item))
            scored.sort(reverse=True, key=lambda x: x[0])
            return [x[1] for x in scored[:top_k]]

        return []


if __name__ == "__main__":
    args = sys.argv[1:]
    top_k = 3
    if "--top-k" in args:
        idx = args.index("--top-k")
        top_k = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    query = " ".join(args) if args else "global security intelligence"
    results = retrieve(query, top_k=top_k)

    print(json.dumps(results, indent=2))
