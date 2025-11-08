# script to go over Elastic index and Index all DWG files using command line
import os,sys
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)  # insert at front to prioritize
print("Script directory:", script_dir)
from __init__ import EsClient, CONFIG
import subprocess
import json
import argparse


def get_dwgs(es_client, index_name):
    query = {
        "query": {
            "term": {
                "file.extension": "dwg"
            }
        }
    }
    response = es_client.search(index=index_name, body=query, size=10000)
    # return all hits, make sure they DO NOT have content already
    hits = [hit for hit in response['hits']['hits']]
    for hit in response['hits']['hits']:
        if "dwg_indexed" in hit['_source']:
            continue
        ajr = hit['_source']
        ajr["id"] = hit["_id"]
        yield ajr


def index_dwg(path: str):
    """Index a single DWG file using .NET exe"""
    config = CONFIG["dwg_indexer"]
    # Ensure the path is correct and you have execution permissions
    exe_path = config["path"]
    if not os.access(exe_path, os.X_OK):
        raise PermissionError(f"Cannot execute: {exe_path}. Check file permissions.")
    process = subprocess.run([exe_path, path, config["fonts_csv"], config["fonts_dir"]], capture_output=True, text=True)
    output = process.stdout.strip()
    try:
        result = json.loads(output)
    except json.JSONDecodeError:
        result = {"error": "Failed to parse output", "raw": output}
    return result

def update_dwg(es_client, file_id: str, index_name: str, content: dict):
    """Update a DWG (with file id) with content dictionary"""
    update_body = {
        "doc": {
            "dwg_content": content,
            "dwg_indexed": True
        }
    }
    print(f"updating {index_name}/{file_id} with {len(str(content))} content characters")
    es_client.update(index=index_name, id=file_id, body=update_body)
def Update_all_dwgs_dwgs(es_client, index_name):
    dwgs = list(get_dwgs(es_client, index_name))
    ndwgs = len(dwgs)
    print(f"*** START INDEXING {ndwgs} DWG FILES FOR INDEX {index_name}***")
    for dwg in dwgs:
        file_path = dwg.get("path", {}).get("real")
        file_id = dwg.get("id")
        if file_path and file_id:
            content = index_dwg(file_path)
            update_dwg(es_client, file_id, index_name, content)
    print(f"*** DONE INDEXING {ndwgs} DWG FILES FOR INDEX {index_name}***")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index DWG files from Elastic index.")
    parser.add_argument("index_name", help="Name of the Elastic index to search for DWG files")
    args = parser.parse_args()
    Update_all_dwgs(EsClient, args.index_name)
    
