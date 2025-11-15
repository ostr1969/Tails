import json,sys,os,docker,subprocess
from elasticsearch import Elasticsearch
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)  # insert at front to prioritize
from __init__ import app, EsClient, CONFIG,wait_for_es
json_path = "fscrawler_templates.json"


  
os.environ["STACK_VERSION"] = CONFIG["docker_env"]["STACK_VERSION"]
os.environ["LICENSE"] = CONFIG["docker_env"]["LICENSE"]
os.environ["ES_PORT"] = CONFIG["docker_env"]["ES_PORT"]
os.environ["CLUSTER_NAME"] = CONFIG["docker_env"]["CLUSTER_NAME"]
os.environ["MEM_LIMIT"] = CONFIG["docker_env"]["MEM_LIMIT"]  
os.environ["ES_PATH"] = os.path.abspath("..\\es_data")

# Optionally, you can change the log level settings
#subprocess.run(["docker", "network", "create", "tails_net"], check=True)
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



FS_JAVA_OPTS = CONFIG["docker_env"]["FS_JAVA_OPTS"]
FSCRAWLER_VERSION = CONFIG["docker_env"]["FSCRAWLER_VERSION"]
FSCRAWLER_PORT = CONFIG["docker_env"]["FSCRAWLER_PORT"]  
DOCS_FOLDER= os.path.abspath("C:\\install\\Pdfs\\try1")
FSCRAWLER_CONFIG= os.path.abspath("..\\fsjobs")

subprocess.run(["docker", "run", "-d", "--name", "fs", 
                "--env", f"FS_JAVA_OPTS={FS_JAVA_OPTS}", 
                "-v", f"{DOCS_FOLDER}:/tmp/es:ro", 
                "-v", f"{FSCRAWLER_CONFIG}:/root/.fscrawler",
                "-p", f"{FSCRAWLER_PORT}:8080", 
                "--rm",
                "--network", "tails_net", 
                f"dadoonet/fscrawler:{FSCRAWLER_VERSION}", 
                newname, "--restart", "--loop", "1"])