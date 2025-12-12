from multiprocessing import Pool
from texttokens import chunk_by_tokens
from embedder import embed_ollama
CHUNK_SIZE = 300
OVERLAP = 50
SEMANTIC_INDEX = "try_chunks"
def process_document(hit):
    """Worker: chunk + embed → return list of ES actions."""
    doc_id = hit["_id"]
    content = hit["_source"].get("content", "")
    if not content.strip():
        return []

    chunks = chunk_by_tokens(content, CHUNK_SIZE, OVERLAP)

    actions = []
    for i, chunk in enumerate(chunks):
        vec = embed_ollama(chunk)

        actions.append({
            "_index": SEMANTIC_INDEX,
            "_source": {
                "doc_id": doc_id,
                "chunk_id": i,
                "content_chunk": chunk,
                "vector": vec
            }
        })

    return actions

