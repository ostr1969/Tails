from shutil import copyfile
import os,sys,time,json
from sentence_transformers import SentenceTransformer
from threading import Thread
from elasticsearch import NotFoundError
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)  # insert at front to prioritize
tess_data_path=os.path.join(script_dir,"..","Tesseract-OCR","tessdata")  
tess_path=os.path.join(script_dir,"..","Tesseract-OCR")  
from flask import render_template, request, send_file, jsonify, url_for, redirect,Flask
from __init__ import app, EsClient, CONFIG,is_es_alive,wait_for_es
from SearchHit import hits_from_resutls
import fscrawlerUtils as fsutils
global model
#from tkinter import filedialog
#app = Flask(__name__)



@app.route('/', methods=['GET', 'POST'])
def search():
    # Pagination
    print(f"home page {request.method}")
    page = int(request.args.get('page', 1))
    start = (page - 1) * CONFIG["results_per_page"]
    end = start + CONFIG["results_per_page"]
    #print(request.form)
    if request.method == 'POST':
        query = request.form['query']
        query_type = request.form.get('query_type', 'match')
    else:
        query = request.args.get('query', "")
        query_type = request.args.get('query_type', 'match')
        
    if len(query) == 0:
        return render_template('search.html', hits=[], total_hits=0, page=1, query="", results_per_page=CONFIG["results_per_page"])
    
    # Build the query based on the selected query type
    query_body = build_query(query, query_type)
    highlight_query=build_query(query, "multi_match" )
    highlight_query["multi_match"]["analyzer"]="stop"
    print("Highlight query:", json.dumps(highlight_query, indent=2))
    fields={field: {"highlight_query": highlight_query} for field in CONFIG["highlight_fields"]}
   
    print("Query body:", json.dumps(query_body, indent=2))
    highlight={
            'fields': fields,
            'pre_tags': ['<em class="highlight">'],
            'post_tags': ['</em>']
            
    }
    
    # Perform a simple query on the 'your_index_name' index
    with open("debug_query.es", "w", encoding="utf-8") as f:
        json.dump({"query":query_body,"highlight":highlight,"size":1000}, f, ensure_ascii=False, indent=2)
    result = EsClient.search(index=CONFIG["index"],query=query_body, 
                             highlight=highlight,size=1000)

    # in case the highlight failed, try to run query without highlighting 
    if len(result["hits"]["hits"]) == 0:
        result = EsClient.search(index=CONFIG["index"], query=query_body ,
            size=1000
        )

    # Extract relevant information from the result
    hits = hits_from_resutls(result)
    # make hits fit in page
    total_hits = len(hits)
    hits = hits[start:end]
    return render_template('search.html',  hits=hits, total_hits=total_hits, page=page, query=query, results_per_page=CONFIG["results_per_page"], query_type=query_type)

@app.route('/view/<index>/<file_id>', methods=['GET'])
def view(index: str, file_id: str):
    """endpoint for viewing file"""
    hit = EsClient.get(index=index, id=file_id)
    path = hit["_source"]["path"]["real"]
    # change base path in case files were moved after indexing
    for base_path, new_path in CONFIG["base_paths"]:
        if path.lower().startswith(base_path.lower()):
            path = path.replace(base_path, new_path)
    ext = hit["_source"]["file"]["extension"]
    target = "files/{}.{}".format(file_id, ext)
    copyfile(path, target)
    if ext.lower() in CONFIG["open_file_types"]:
        download = False
    else:
        download = True
    return send_file(target, as_attachment=download)

@app.route('/more/<index>/<file_id>', methods=['POST','GET'])
def more(index: str, file_id: str):
    #hit = EsClient.get(index=index, id=file_id)
    page = int(request.args.get('page', 1))
    start = (page - 1) * CONFIG["results_per_page"]
    end = start + CONFIG["results_per_page"]
    query_body={
    "more_like_this": {
      "fields": ["title", "content"],
      "like": [
        { "_index": index, "_id": file_id }       
      ]
    }
    }
    result = EsClient.search(index=CONFIG["index"], query=query_body ,
            size=1000
        )
    hits = hits_from_resutls(result)
    total_hits = len(hits)
    hits = hits[start:end]
    return render_template('search.html',  hits=hits, total_hits=total_hits, page=page, query="", results_per_page=CONFIG["results_per_page"], query_type="more_like_this")

@app.route('/index', methods=['GET', 'POST'])
def fscraller_index():
    print(f"index page {request.method}")
    if request.method == "POST":
        name = request.form["jobName"]
        target_dir = request.form["targetDirectory"]
        useocr= "doOcr" in request.form
        if useocr:
            print("Using OCR")
        else:
            print("Not using OCR")
        
        if fsutils.create_new_job(name):
            fsutils.load_defaults_to_job(name)
            fsutils.edit_job_setting(name, "fs.url", target_dir)
            fsutils.edit_job_setting(name, "fs.ocr.enabled", useocr)
            fsutils.edit_job_setting(name, "fs.ocr.data_path", tess_data_path)
            fsutils.edit_job_setting(name, "fs.ocr.path", tess_path)            
            fsutils.run_job(name,model)
    CONFIG["index"] = fsutils.get_all_jobs()
    return render_template("fscrawler.html",j=0)

@app.route('/stat', methods=['GET'])
def stat():
    return "OK"
@app.route('/reset', methods=['GET'])
def reset():
    print("Resetting FSCrawler jobs")
    return render_template("fscrawler.html",j=1)

@app.route('/_existing_jobs', methods=['GET'])
def existing_jobs_info():
    #print("Gathering existing fscrawler jobs information")
    stats = fsutils.jobs_status()
    return jsonify(stats)

@app.route('/_elasticsearch_statistics', methods=['GET'])
def index_statistics():
    #print("Gathering elasticsearch statistics")
    # Get total number of documents
    total_documents = get_total_documents(CONFIG["index"])
    # Get total number of documents with content (adjust the query as needed)
    if total_documents == 0:
        return {
            "total_documents": 0,
            "total_documents_with_content": 0,
            "file_extensions": []
        }
    total_documents_with_content = EsClient.count(index=CONFIG["index"], query={"exists": {"field": "content"}})['count']
    
    # Get file extensions distribution
    file_extensions_aggregation = EsClient.search(index=CONFIG["index"],size=0, aggs={        
        "file_extensions": {
            "terms": {
                "field": "file.extension",
                "size": 9
                }            }        }
    )

    if 'aggregations' not in file_extensions_aggregation:
        return {
            "total_documents": total_documents,
            "total_documents_with_content": total_documents_with_content,
            "file_extensions": []
        }
    file_extensions_buckets = file_extensions_aggregation['aggregations']['file_extensions']['buckets']
    # addint the "other" count
    file_extensions_buckets.append({"key": "other", "doc_count": file_extensions_aggregation['aggregations']['file_extensions']["sum_other_doc_count"]})
    file_extensions_stats = [{"extension": bucket['key'], "count": bucket['doc_count']} for bucket in file_extensions_buckets]

    # Combine all statistics
    return {
        "total_documents": total_documents,
        "total_documents_with_content": total_documents_with_content,
        "file_extensions": file_extensions_stats
    }

@app.route('/delete_job/<job_name>', methods=['GET'])
def delete_job(job_name: str):
    fsutils.delete_job(job_name)
    folder_path = os.path.join(CONFIG["fscrawler"]["config_dir"], job_name)
    if os.path.exists(folder_path):
        print(f"Folder exists at {folder_path}, deletion may have failed.")
    else:
        print(f"Folder does not exist at {folder_path}, deletion successful.")
    
    return redirect(url_for('fscraller_index'))

def build_query(query_text, query_type):
    global model
    fields = CONFIG["search_fields"]
    if model is None and query_type == "Semantic":
        print("Model not loaded yet, using default match query.")
        query_type = "multi_match"
    if query_type == "fuzzy":
        return {
            "multi_match": {
                "query": query_text,
                "fields": fields,
                "fuzziness": "AUTO"
            }
        }

    elif query_type == "phrase":
        return {
            "multi_match": {
                "query": query_text,
                "fields": fields,
                "type": "phrase"
            }
        }
    elif query_type == "semantic":
        #print(f"Building semantic query {query_text} {CONFIG['semantic_model']['content_embedding_field']} {CONFIG['semantic_model']['filename_embedding_field']}")
        query_vector = model.encode(query_text).tolist()
        #print("Query vector :", query_vector)
        return {
            "script_score": {
               "query": {
            "exists": {
              "field": "has"
            }
          },
                "script": {
                    "source": """double s1=cosineSimilarity(params.query_vector, '{}')+1 ; 
                    double s2=cosineSimilarity(params.query_vector, '{}')+1 ;
                     return Math.max(s1, s2);""".format(CONFIG["semantic_model"]["content_embedding_field"], 
                                                        CONFIG["semantic_model"]["filename_embedding_field"]),
                    "params": {"query_vector": query_vector}
                }
            }
        }
    elif query_type == "function_score":
        query_vector = model.encode(query_text).tolist()
        return {
            "function_score": {
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": fields,
                        
                    }
                },
                "boost_mode": "multiply",
                "functions": [
                    {
            "script_score": {
              
                "script": {
                    "source": """double s1=cosineSimilarity(params.query_vector, '{}')+1 ; 
                    double s2=cosineSimilarity(params.query_vector, '{}')+1 ;
                     return Math.max(s1, s2);""".format(CONFIG["semantic_model"]["content_embedding_field"], 
                                                        CONFIG["semantic_model"]["filename_embedding_field"]),
                    "params": {"query_vector": query_vector}
                }
            }
        }
                ]
            }
        }    
    elif query_type == "wildcard":
        # Wildcard doesn't support multi_match — build OR terms per field
        should_clauses = [{"wildcard": {f: f"{query_text}*"}} for f in fields]
        return {"bool": {"should": should_clauses}}

    elif query_type == "regexp":
        should_clauses = [{"regexp": {f: query_text}} for f in fields]
        return {"bool": {"should": should_clauses}}

    elif query_type == "more_like_this":
        print("Building more_like_this query with fields:", fields)
        return {
            "more_like_this": {
                "fields": fields,
                "like": query_text,
                "min_term_freq": 1,
                "max_query_terms": 25
            }
        }

    elif query_type == "query_string":
        return {
            "query_string": {
                "query": query_text,
                "fields": fields
            }
        }

    else:
        # Default: match on all fields
        return {
            "multi_match": {
                "query": query_text,
                "fields": fields
            }
        }
def get_total_documents(index_name):
    try:
        return EsClient.count(index=index_name)['count']
    except NotFoundError:
        return 0
def background_task():
    print("Background thread running...")
    # Do something useful here

def load_model():
    global model
    print("Loading model...")
    model = SentenceTransformer(CONFIG["semantic_model"]["model_name"])
    #time.sleep(10)
    print("Model loaded.")


       
if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    #load_model()                # runs once
        Thread(target=load_model, daemon=True).start()  # runs once
    if not is_es_alive(EsClient):
        print("Elasticsearch is not reachable. start outside with the start_elastic.bat script") 
        sys.exit(1)    
    app.run(debug=True)
