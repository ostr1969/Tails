import json,sys,os,docker,subprocess
from elasticsearch import Elasticsearch
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)  # insert at front to prioritize
from __init__ import app, EsClient, CONFIG,wait_for_es
json_path = "fscrawler_templates.json"


STACK_VERSION="9.2.0"   
os.environ["STACK_VERSION"] = STACK_VERSION
os.environ["LICENSE"] = "trial"
os.environ["ES_PORT"] = "9200" 
os.environ["CLUSTER_NAME"] = "es"
os.environ["MEM_LIMIT"] = "4294967296"
os.environ["FS_JAVA_OPTS"] = "-DLOG_LEVEL=debug -DDOC_LEVEL=debug"
os.environ["FSCRAWLER_VERSION"] = "2.10-SNAPSHOT"
os.environ["FSCRAWLER_PORT"] = "8080"
os.environ["DOCS_FOLDER"] = os.path.abspath("C:\\install\\Pdfs\\try1")
os.environ["FSCRAWLER_CONFIG"] = os.path.abspath("..\\fsjobs")
env={"STACK_VERSION": STACK_VERSION, "LICENSE": "trial", "ES_PORT": "9200",
     "CLUSTER_NAME": "es", "MEM_LIMIT": "4294967296",
     "FS_JAVA_OPTS": "-DLOG_LEVEL=debug -DDOC_LEVEL=debug",
     "FSCRAWLER_VERSION": "2.10-SNAPSHOT",
     "FSCRAWLER_PORT": "8080",
     "DOCS_FOLDER": os.path.abspath("C:\\install\\Pdfs\\try1"),
     "FSCRAWLER_CONFIG": os.path.abspath("..\\fsjobs")}
# Optionally, you can change the log level settings

subprocess.run(["docker", "compose","-f", "crawler.yml" ,"up", "-d","es"], check=True)
wait_for_es(EsClient)
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
newname="phd"
templates = data.get("component_templates", [])
for tpl in templates:
    name = tpl["name"].replace("try1", newname)
    body = tpl["component_template"]

    print(f"Uploading component template: {name}")
    response=EsClient.cluster.put_component_template(        name=name, body=body)
   

    print(f" → Elasticsearch response: {response}")



env={"FSCRAWLER_VERSION": "2.10-SNAPSHOT",
     "FSCRAWLER_PORT": "8080",
     "DOCS_FOLDER": os.path.abspath("C:\\install\\Pdfs\\try1"),
     "FSCRAWLER_CONFIG": os.path.abspath("..\\fsjobs")}
subprocess.run(["docker", "compose","-f", "crawler.yml" ,"up", "-d","fs"], check=True)
