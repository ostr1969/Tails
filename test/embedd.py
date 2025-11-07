from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
ES_HOST = "http://localhost:9200"      # Your Elasticsearch URL
INDEX_NAME = "articles"          # Replace with your index name
CONTENT_FIELD = "content"
FILENAME_FIELD = "file.filename"
CONTENT_EMBEDDING = "content_embedding"
FILENAME_EMBEDDING = "filename_embedding"
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

for doc in scroll:  # scroll:
    doc_id = doc["_id"]
    source = doc["_source"]
    context_text = source.get(CONTENT_FIELD, "").replace("\n", " ")
    filename_text = source.get(FILENAME_FIELD, "").replace("\n", " ")

    if not context_text :
        continue  # skip empty content

    count += 1
    if count>1000:
        continue
    
    action={
        "_op_type": "update",
        "_index": INDEX_NAME,
        "_id": doc_id}
    embedding1 = model.encode(context_text).tolist()
    embedding2 = model.encode(filename_text).tolist()
    action["doc"] = {CONTENT_EMBEDDING: embedding1,FILENAME_EMBEDDING: embedding2,"has": True}
    actions.append(action)
   
    print(f"Prepared update for document ID: {doc_id}")
    
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
          "field": "has"
        }
      },
            "script": {
                "source":
                    """
                    double s1=cosineSimilarity(params.query_vector, 'content_embedding') ;
                    double s2=cosineSimilarity(params.query_vector, 'filename_embedding') ;
                    return Math.max(s1, s2);
                    """,
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