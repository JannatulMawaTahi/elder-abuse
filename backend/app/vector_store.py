"""
Vector Store — ChromaDB semantic search over Bangladesh legal sections.

Builds a ChromaDB collection from act_knowledge_base.json (Phase 1 Step 4),
embedding each PMA/BPC section with a multilingual model so that complaints
in Bangla, English, or Mixed — even with Whisper typos — match the right law.

Model : paraphrase-multilingual-MiniLM-L12-v2 (free, local, 384-dim, 50+ langs)
Store : backend/vector_store/ (gitignored)

First run downloads the model (~120 MB). Subsequent runs load from cache.
"""

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions


# ── Constants ─────────────────────────────────────────────────────────────────
KB_PATH         = Path(__file__).parent.parent / "phase1_outputs" / "act_knowledge_base.json"
KW_PATH         = Path(__file__).parent.parent / "phase1_outputs" / "keyword_dictionary.json"
STORE_PATH      = Path(__file__).parent.parent / "vector_store"
COLLECTION_NAME = "legal_sections"
EMBED_MODEL     = "paraphrase-multilingual-MiniLM-L12-v2"


# ── Lazy singletons ───────────────────────────────────────────────────────────
_embed_fn = None
_collection = None


def _get_embed_fn():
    """Lazy-init the sentence-transformer embedding function."""
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
    return _embed_fn


def _load_category_keywords() -> dict[str, str]:
    """
    Load keyword_dictionary.json → {category: "kw1 kw2 kw3 ..."}.

    These complaint-style keywords are appended to each legal section's
    embedded document, bridging the gap between everyday complaint language
    and formal legal text (and absorbing Whisper spelling variations).
    """
    if not KW_PATH.exists():
        return {}
    with open(KW_PATH, encoding="utf-8") as f:
        kw = json.load(f)
    out: dict[str, str] = {}
    for category, groups in kw.items():
        words = (
            groups.get("bangla", []) +
            groups.get("english", []) +
            groups.get("mixed_forms", [])
        )
        out[category] = " ".join(words)
    return out


def _build_documents(kb: dict[str, Any]) -> tuple[list[str], list[dict], list[str]]:
    """
    Convert knowledge base into (documents, metadatas, ids) for ChromaDB.

    Each document = section title + Bangla legal text + English legal text
    + complaint-style keywords for the categories this section applies to.
    The keyword enrichment is what makes real-world complaints (and Whisper
    typos) match the right law instead of generic 'Definitions' sections.
    """
    cat_keywords = _load_category_keywords()

    documents, metadatas, ids = [], [], []
    for key, val in kb.items():
        applicable = val.get("applicable_for", [])

        # Collect complaint keywords for the specific categories this law covers.
        # Skip 'all' (procedural sections like Definitions/Penalty) so they
        # don't get enriched with everything and dominate every search.
        enrich_parts = []
        for cat in applicable:
            if cat != "all" and cat in cat_keywords:
                enrich_parts.append(cat_keywords[cat])
        enrichment = "  ".join(enrich_parts)

        combined = (
            f"{val.get('section', '')}\n"
            f"{val.get('text', '')}\n"
            f"{val.get('text_english', '')}"
        )
        if enrichment:
            combined += f"\nসংশ্লিষ্ট অভিযোগ / Related complaints: {enrichment}"

        documents.append(combined)
        metadatas.append({
            "section":        val.get("section", ""),
            "applicable_for": ",".join(applicable),  # list→str (Chroma requirement)
            "severity_min":   int(val.get("severity_min", 1)),
            "law":            "PMA" if key.startswith("pma") else "BPC",
        })
        ids.append(key)
    return documents, metadatas, ids


def build_store(force_rebuild: bool = False) -> dict[str, Any]:
    """
    Build (or load) the ChromaDB vector store from act_knowledge_base.json.

    Args:
        force_rebuild : If True, delete & recreate even if it already exists.

    Returns:
        {"status": "built"|"loaded", "count": 16, "collection": "legal_sections"}
    """
    global _collection

    if not KB_PATH.exists():
        raise FileNotFoundError(f"Knowledge base not found: {KB_PATH}")

    client = chromadb.PersistentClient(path=str(STORE_PATH))
    embed_fn = _get_embed_fn()

    # If exists and not forcing rebuild → just load
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing and not force_rebuild:
        _collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=embed_fn
        )
        return {
            "status":     "loaded",
            "count":      _collection.count(),
            "collection": COLLECTION_NAME,
        }

    # Rebuild path
    if COLLECTION_NAME in existing:
        client.delete_collection(name=COLLECTION_NAME)

    _collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )

    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)

    documents, metadatas, ids = _build_documents(kb)
    _collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return {
        "status":     "built",
        "count":      _collection.count(),
        "collection": COLLECTION_NAME,
    }


def _get_collection():
    """Return the active collection, building/loading if needed."""
    global _collection
    if _collection is None:
        build_store()
    return _collection


def search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """
    Semantic search: return the top_k most relevant legal sections for a query.

    Returns a list of:
        {
            "id":         "bpc_323",
            "section":    "BPC Section 323 — ...",
            "law":        "BPC",
            "applicable_for": ["physical"],
            "severity_min":   4,
            "similarity":  0.91,        # 1.0 = identical, higher = closer
            "text":       "...(combined doc)..."
        }
    """
    if not query or not query.strip():
        return []

    collection = _get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    out: list[dict[str, Any]] = []
    ids        = results["ids"][0]
    documents  = results["documents"][0]
    metadatas  = results["metadatas"][0]
    distances  = results["distances"][0]

    for i in range(len(ids)):
        meta = metadatas[i]
        applicable = meta.get("applicable_for", "")
        out.append({
            "id":             ids[i],
            "section":        meta.get("section", ""),
            "law":            meta.get("law", ""),
            "applicable_for": applicable.split(",") if applicable else [],
            "severity_min":   meta.get("severity_min", 1),
            "similarity":     round(1.0 - distances[i], 3),  # cosine distance → similarity
            "text":           documents[i],
        })
    return out


# ── CLI for manual build / test ───────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    print(f"Building vector store from: {KB_PATH.name}")
    info = build_store(force_rebuild="--rebuild" in sys.argv)
    print(f"  Status: {info['status']}  |  Sections: {info['count']}")

    print("\nSample searches:")
    for q in [
        "ছেলে আমাকে মার্ধুর করেছে",          # Whisper typo for মারধর
        "son threw me out of the house",
        "জমির দলিল জোর করে লিখিয়ে নিয়েছে",
    ]:
        print(f"\n  Query: {q}")
        for r in search(q, top_k=3):
            print(f"    [{r['similarity']:.2f}] {r['id']:<10} {r['section'][:50]}")
