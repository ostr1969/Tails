from embedder import embed_ollama
from elasticsearch import Elasticsearch

ES_URL = "http://localhost:9200"
query_text = "convert the PostScript back to PDF "
SEMANTIC_INDEX = "try_chunks"

es = Elasticsearch(ES_URL)

query_vec = embed_ollama(query_text)

body = {
    "size": 3,
    "query": {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.q, 'vector') + 1.0",
                "params": {"q": query_vec}
            }
        }
    }
}

resp = es.search(index=SEMANTIC_INDEX, body=body)

for h in resp["hits"]["hits"]:
    print("Score:", h["_score"])
    print("Doc:", h["_source"]["doc_id"])
    print("Chunk:", h["_source"]["content_chunk"])
    print()