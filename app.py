from shutil import copyfile
import os
from flask import render_template, request, send_file, jsonify
from __init__ import app, EsClient, CONFIG
from SearchHit import hits_from_resutls
import fscrawlerUtils as fsutils
import tkinter
from tkinter import filedialog



@app.route('/', methods=['GET', 'POST'])
def search():
    # Pagination
    page = int(request.args.get('page', 1))
    start = (page - 1) * CONFIG["results_per_page"]
    end = start + CONFIG["results_per_page"]

    if request.method == 'POST':
        query = request.form['query']
    else:
        query = request.args.get('query', "")

    if len(query) == 0:
        return render_template('search.html', hits=[], total_hits=0, page=1, query="", results_per_page=CONFIG["results_per_page"])

    # Perform a simple query on the 'your_index_name' index
    result = EsClient.search(index=CONFIG["index"], body={
        'query': {
            'query_string': {
                'query': query,
                'fields': CONFIG["search_fields"]
            }
        },
        'size': 1000,
        'highlight': {
            'fields': {field: {} for field in CONFIG["highlight_fields"]},
            'pre_tags': ['<em class="highlight">'],
            'post_tags': ['</em>']
        }
    })

    # in case the highlight failed, try to run query without highlighting 
    if len(result["hits"]["hits"]) == 0:
        result = EsClient.search(index=CONFIG["index"], body={
            'query': {
                'query_string': {
                    'query': query,
                    'fields': CONFIG["search_fields"]
                }
            },
            'size': 1000,
        })  

    # Extract relevant information from the result
    hits = hits_from_resutls(result)
    # make hits fit in page
    total_hits = len(hits)
    hits = hits[start:end]
    return render_template('search.html',  hits=hits, total_hits=total_hits, page=page, query=query, results_per_page=CONFIG["results_per_page"])

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

@app.route('/index', methods=['GET', 'POST'])
def fscraller_index():
    if request.method == "POST":
        name = request.form["jobName"]
        target_dir = request.form["targetDirectory"]
        #print(request.form["design"])
        if fsutils.create_new_job(name):
            fsutils.load_defaults_to_job(name)
            fsutils.edit_job_setting(name, "fs.url", target_dir)
            fsutils.run_job(name)
    CONFIG["index"] = fsutils.get_all_jobs()
    return render_template("fscrawler.html",j=0)

@app.route('/stat', methods=['GET'])
def stat():
    return "OK"
@app.route('/reset', methods=['GET'])
def reset():
    
    return render_template("fscrawler.html",j=1)

@app.route('/_existing_jobs', methods=['GET'])
def existing_jobs_info():
    stats = fsutils.jobs_status()
    return jsonify(stats)

@app.route('/_elasticsearch_statistics', methods=['GET'])
def index_statistics():
    # Get total number of documents
    total_documents = EsClient.count(index=CONFIG["index"])['count']

    # Get total number of documents with content (adjust the query as needed)
    total_documents_with_content = EsClient.count(index=CONFIG["index"], body={"query": {"exists": {"field": "content"}}})['count']

    # Get file extensions distribution
    file_extensions_aggregation = EsClient.search(index=CONFIG["index"], body={
        "size": 0,
        "aggs": {
            "file_extensions": {
                "terms": {
                    "field": "file.extension",
                    "size": 9
                }
            }
        }
    })


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
    return True


if __name__ == '__main__':
    app.run(debug=True)
