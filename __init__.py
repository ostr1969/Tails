import os
from flask import Flask
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import json
from threading import Thread
import inspect

def who_called_me():
    # Get the caller's frame (1 level up)
    caller_frame = inspect.stack()[1]
    caller_name = caller_frame.function
    print(f"Called by: {caller_name}")
#import tkinter
#from tkinter import filedialog



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

def init_llm():
        app = Flask(__name__)
        if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Setup code here, e.g., database initialization
            with app.app_context():
                start_background_loading()  # Example function to initialize a database
        return app 
        
def start_background_loading():    
    thread = Thread(target=load_model_background)
    thread.daemon = True  # so Flask can still exit cleanly
    thread.start()      
def load_model_background():
    global model
    print("Background model loading started...")    
    model = SentenceTransformer(CONFIG["semantic_model"]["model_name"])
    print("Model loaded successfully.")
   

