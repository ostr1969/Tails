import os,sys,time
#script_dir = os.path.dirname(os.path.abspath(__file__))
#if script_dir not in sys.path:
#    sys.path.insert(0, script_dir)  # insert at front to prioritize
from __init__ import EsClient, CONFIG, index_exists,wait_for_es
import subprocess
import json
import argparse
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
# CONFIG = {}
# with open("config.json") as f:
#     CONFIG = json.load(f)
CONTENT_FIELD = CONFIG["semantic_model"]["content_field"]
FILENAME_FIELD = CONFIG["semantic_model"]["filename_field"]
CONTENT_EMBEDDING = CONFIG["semantic_model"]["content_embedding_field"]
FILENAME_EMBEDDING = CONFIG["semantic_model"]["filename_embedding_field"]
MODEL_NAME = CONFIG["semantic_model"]["model_name"]
#EsClient = Elasticsearch(CONFIG["elasticsearch_url"])

def build_action(doc,index, model):
    doc_id = doc["_id"]
    source = doc["_source"]
    context_text = source.get(CONTENT_FIELD, "").replace("\n", " ")
    filename_text = source.get(FILENAME_FIELD, "").replace("\n", " ")

    if not context_text :
        return None  # skip empty content

    action={
        "_op_type": "update",
        "_index": index,
        "_id": doc_id}
    embedding1 = model.encode(context_text).tolist()
    embedding2 = model.encode(filename_text).tolist()
    action["doc"] = {CONTENT_EMBEDDING: embedding1,FILENAME_EMBEDDING: embedding2,"has": True}
    return action
def Update_all_semantics(es_client, index_name,model):
    query={"query": {"exists": {"field": "content"}}}
    # note: es query and scan query built differently
    total_documents_with_content = es_client.count(index=index_name, query=query["query"])['count']
    scroll = helpers.scan(client=es_client, index=index_name, query=query, preserve_order=False)
    print(f"*** START INDEXING SEMANTIC EMBEDDINGS FOR INDEX {index_name}, total documents: {total_documents_with_content}")
    actions=[]
   
    count = 0
    start_time=time.time()
    #model = SentenceTransformer(MODEL_NAME)
    for doc in scroll:
        action = build_action(doc, index_name, model)
        if action is None:
            continue
        count += 1
        actions.append(action)
        if len(actions)>=100:
            helpers.bulk(es_client, actions)
            actions = []
            print(f"Processed {count} documents in {time.time()-start_time:.2f} seconds...")
            start_time=time.time()
    if actions:
        print(f"Processing final batch of {len(actions)} documents...")
        helpers.bulk(es_client, actions)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="reIndex semantic from Elastic index.")
    parser.add_argument("index_name", help="Name of the Elastic index to add semantic embeddings")
    args = parser.parse_args()
    # --- INITIALIZE ---
    print(f"Start Creating Semantic Embeddings...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded ✅")
    # --- SCROLL THROUGH ALL DOCUMENTS ---
    Update_all_semantics(EsClient, args.index_name,model)