import json,sys,os,docker
from elasticsearch import Elasticsearch
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)  # insert at front to prioritize
from __init__ import app, EsClient, CONFIG
json_path = "fscrawler_templates.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
newname="phd"
templates = data.get("component_templates", [])
for tpl in templates:
    name = tpl["name"].replace("try1", newname)
    body = tpl["component_template"]

    print(f"Uploading component template: {name}")
   # response=EsClient.cluster.put_component_template(        name=name, body=body)
   

    #print(f" → Elasticsearch response: {response}")

STACK_VERSION="9.2.0"    
client = docker.from_env()
client.networks.create("tails_net", driver="bridge")
client.volumes.create(name="esdata")
container = client.containers.run(image=f"docker.elastic.co/elasticsearch/elasticsearch:{STACK_VERSION}",
        name="es",
        ports={'9200/tcp': 9200},
        environment={
        "node.name=elasticsearch",
        "cluster.name=tails",
       "cluster.initial_master_nodes=elasticsearch",
       "bootstrap.memory_lock=true",
       "xpack.security.enabled=false",
       "xpack.security.http.ssl.enabled=false",
       "xpack.security.transport.ssl.enabled=false",
       "xpack.license.self_generated.type=trial"},
        detach=True,
        network="tails_net",
        volumes={"esdata": {"bind": "/usr/share/elasticsearch/data", "mode": "rw"}},
        ulimits=[docker.types.Ulimit(name='memlock', soft=-1, hard=-1)],
        mem_limit=4294967296,
        healthcheck={"test": ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"], "interval": 3000000000, "timeout": 1000000000, "retries": 5}
                                  )