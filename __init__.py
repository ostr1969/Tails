import os,time
from flask import Flask
from elasticsearch import Elasticsearch
#from sentence_transformers import SentenceTransformer
import json, subprocess
#from threading import Thread

#import tkinter
#from tkinter import filedialog
app = Flask(__name__)


# read settings from json
CONFIG = {}
with open("config.json") as f:
    CONFIG = json.load(f)
curdir = os.getcwd()
drive, path = os.path.splitdrive(curdir)
#"exe": "\\..\\fscrawler\\bin\\fscrawler.bat",
#"config_dir": "\\..\\fsjobs",
#"defaults": "\\..\\fsjobs\\_defaults.yaml"

# Connect to your Elasticsearch cluster
EsClient = Elasticsearch(CONFIG["elasticsearch_url"])
# load some dynamic defaults on the CONFIG
PROJECT_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print("PROJECT_PARENT:", PROJECT_PARENT)
if CONFIG["fscrawler"]["exe"] == "None":
    CONFIG["fscrawler"]["exe"] = os.path.join(PROJECT_PARENT, "fscrawler", "bin", "fscrawler.bat")
if CONFIG["fscrawler"]["config_dir"] == "None":
    CONFIG["fscrawler"]["config_dir"] = os.path.join(PROJECT_PARENT, "fsjobs")
if CONFIG["fscrawler"]["defaults"] == "None":
    CONFIG["fscrawler"]["defaults"] = os.path.join(CONFIG["fscrawler"]["config_dir"], "_defaults.yaml")
def wait_for_es(es: Elasticsearch, timeout=60):
    start = time.time()
    while True:
        try:
            if es.ping():
                print("Elasticsearch is ready!")
                return True
        except Exception:
            pass

        if time.time() - start > timeout:
            raise TimeoutError("Elasticsearch did not become ready in time.")

        print("Waiting for Elasticsearch...")
        time.sleep(2)
def is_es_alive(es: Elasticsearch, timeout=10):
    """Return True if Elasticsearch responds to ping within timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if es.ping():
                return True
        except Exception:
            pass
        time.sleep(1)
    return False
def compose_up_es():
    os.environ["STACK_VERSION"] = CONFIG["docker_env"]["STACK_VERSION"]
    os.environ["LICENSE"] = CONFIG["docker_env"]["LICENSE"]
    os.environ["ES_PORT"] = CONFIG["docker_env"]["ES_PORT"]
    os.environ["CLUSTER_NAME"] = CONFIG["docker_env"]["CLUSTER_NAME"]
    os.environ["MEM_LIMIT"] = CONFIG["docker_env"]["MEM_LIMIT"]  
    os.environ["ES_PATH"] = os.path.abspath("..\\es_data")
    subprocess.run(["docker", "compose","-f", "crawler.yml" ,"up", "-d","es"], check=True)
    #wait_for_es(EsClient)