from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
ES_HOST = "http://localhost:9200"      # Your Elasticsearch URL
INDEX_NAME = "articles"          # Replace with your index name
CONTENT_FIELD = "content"
EMBEDDING_FIELD = "embedding"
MODEL_NAME = "C:\\Users\\barako\\.cache\\huggingface\\hub\\models--sentence-transformers--all-MiniLM-L6-v2\\snapshots\\c9745ed1d9f207416be6d2e6f8de32d1f16199bf"

# --- INITIALIZE ---
es = Elasticsearch(ES_HOST)
model = SentenceTransformer(MODEL_NAME)
print("Model loaded ✅")
# --- SCROLL THROUGH ALL DOCUMENTS ---
query = {"query": {"match_all": {}}}
scroll = helpers.scan(client=es, index=INDEX_NAME, query=query, preserve_order=False)

actions = []
count = 0

for doc in []:  # scroll:
    doc_id = doc["_id"]
    source = doc["_source"]
    text = source.get(CONTENT_FIELD)

    if not text:
       
        continue  # skip empty content

    embedding = model.encode(text.replace("\n", " ")).tolist()
    
    actions.append({
        "_op_type": "update",
        "_index": INDEX_NAME,
        "_id": doc_id,
        "doc": {EMBEDDING_FIELD: embedding,"has_embedding": True}
    })
    print(f"Prepared update for document ID: {doc_id}, embedding length: {len(embedding)}")
    count += 1
    # Bulk update in batches of 100
    if len(actions) >= 100:
        helpers.bulk(es, actions)
        print(f"Processed {count} documents...")
        actions = []

# Final batch
if actions:
    print(f"Processing final batch of {len(actions)} documents...")
    helpers.bulk(es, actions)

print(f"Done. Updated embeddings for {count} documents.")

query = "Training strategies for athletes in  basketball, volleyball, and track and field"

query_vector = model.encode(query).tolist()

response = es.search(
    index=INDEX_NAME,
    size=5,
    query={
        "script_score": {
           "query": {
        "exists": {
          "field": "has_embedding"
        }
      },
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": query_vector}
            }
        }
    }
)
print("search query:", query)
#print("query vector :", query_vector)
for hit in response["hits"]["hits"]:
    txt=hit["_source"]["content"].replace("\n", " ")
    print(f"Score: {hit['_score']:.4f} | Content: {hit["_source"]["file"]["filename"]}")