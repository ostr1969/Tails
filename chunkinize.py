from multiprocessing.pool import Pool
from elasticsearch import Elasticsearch, helpers
from vectorizechunks import process_document
ES_URL = "http://localhost:9200"
ORIGINAL_INDEX = "try"
SEMANTIC_INDEX = "try_chunks"

es = Elasticsearch(ES_URL)

# Create semantic index if missing
mapping = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "chunk_id": {"type": "integer"},
            "content_chunk": {"type": "text"},
            "vector": {
                "type": "dense_vector",
                "dims": 768,     # "nomic-embed-text" = 768
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

if not es.indices.exists(index=SEMANTIC_INDEX):
    es.indices.create(index=SEMANTIC_INDEX, body=mapping)


def scroll_source():
    """Generator for documents from original index."""
    scroll = es.search(
        index=ORIGINAL_INDEX,
        scroll="2m",
        size=200,
        body={"query": {"match_all": {}}}
    )
    scroll_id = scroll["_scroll_id"]

    while True:
        hits = scroll["hits"]["hits"]
        if not hits:
            break
        yield hits
        scroll = es.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = scroll["_scroll_id"]


# Multiprocessing pool
pool = Pool(processes=10)  # adjust to your CPU

batch = []

for hits in scroll_source():
    # process all hits in parallel
    results = pool.map(process_document, hits)

    # flatten
    for r in results:
        batch.extend(r)

    # bulk flush
    if len(batch) >= 500:
        helpers.bulk(es, batch)
        batch = []

# final flush
if batch:
    helpers.bulk(es, batch)

pool.close()
pool.join()

es.indices.refresh(index=SEMANTIC_INDEX)
