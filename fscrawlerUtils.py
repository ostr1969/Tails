# this file contains a module for using fscrawler from python
import os,threading,time,json,sys
script_dir = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.join(script_dir, "..", "python", "python.exe")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from __init__ import CONFIG, EsClient,wait_for_es,is_es_alive,win2linux_path,index_exists
from elasticsearch.exceptions import NotFoundError
import shutil,subprocess
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE
import yaml
import regex as re
from index_llm import Update_all_semantics
from index_dwg import Update_all_dwgs_dwgs

FSCRAWLER_JOBS = {}

def get_all_jobs():
    """get all jobs of fscrawler"""
    jobs = []
    base_path = CONFIG["fscrawler"]["config_dir"]
    #print(base_path)
    for obj in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, obj)) and not obj == "_default":
            jobs.append(obj)
    return jobs

def create_new_job(name: str):
    """create a new project for FSCrawler. this is the first step in running it."""
    print(f"Creating new job: {name}")
    #exe_path = CONFIG["fscrawler"]["exe"]
    config_dir = CONFIG["fscrawler"]["config_dir"]
    current_config_dir = os.path.join(config_dir,name)
    if name in FSCRAWLER_JOBS and os.path.isdir(current_config_dir):
        return False
    load_defaults_to_job(name)
    FSCRAWLER_JOBS[name] = None
    print("CREATED DIRECTORY and load default settings AT ", current_config_dir)
    return True
def run_fs_docker_job(name: str,target_dir: str):
    FS_JAVA_OPTS = CONFIG["docker_env"]["FS_JAVA_OPTS"]
    FSCRAWLER_VERSION = CONFIG["docker_env"]["FSCRAWLER_VERSION"]
    FSCRAWLER_PORT = CONFIG["docker_env"]["FSCRAWLER_PORT"]  
    DOCS_FOLDER= os.path.abspath(target_dir)
    FSCRAWLER_CONFIG= os.path.abspath(CONFIG["fscrawler"]["config_dir"])
    
    return subprocess.run(["docker", "run",  "--name", "fs", 
                "--env", f"FS_JAVA_OPTS={FS_JAVA_OPTS}", 
                "-v", f"{DOCS_FOLDER}:{win2linux_path(DOCS_FOLDER)}:ro", 
                "-v", f"{FSCRAWLER_CONFIG}:/root/.fscrawler",
                "-p", f"{FSCRAWLER_PORT}:8080", 
                "--rm",
                "--network", "tails_net", 
                f"dadoonet/fscrawler:{FSCRAWLER_VERSION}", 
                name, "--restart","--silent", "--loop", "1"])
class FscrawlerError (Exception):
    pass

def get_job_settings_path(name: str):
    path = os.path.join(CONFIG["fscrawler"]["config_dir"], name, "_settings.yaml")
    if not os.path.isfile(path):
        raise FscrawlerError(f"Specified project {name} doesn't exist,"+ 
                             "make sure to create it before editing and running:\n"+
                             path)
    return path 

def load_defaults_to_job(name: str):
    """Method to load the default settings to a fscrawler job. they are defined in the CONFIG json"""
    # loading everything from the defaults file
    with open(CONFIG["fscrawler"]["defaults"], "r") as f:
        d = yaml.safe_load(f)
    # changing elasticsearch adress to the one in CONFIG
    elastic_url=f"http://{CONFIG["docker_env"]["CLUSTER_NAME"]}:{CONFIG["docker_env"]["ES_PORT"]}"
    d["elasticsearch"]["urls"] = [elastic_url]
    # setting name to proper name
    d["name"] = name
    # dumping settings to project dir
    jobDir=os.path.join(CONFIG["fscrawler"]["config_dir"], name)
    settingDir=os.path.join(CONFIG["fscrawler"]["config_dir"], name,"_settings.yaml")
    if not os.path.isdir(jobDir):
        os.mkdir(jobDir)
    with open(settingDir, "w") as f:
        yaml.dump(d, f)
    print("Loaded default settings to", settingDir)    

def get_job_setting(name: str, key: str):
    with open(get_job_settings_path(name), "r") as f:
        ajr = yaml.safe_load(f)
    # change setting
    key_vec = key.split(".")
    if len(key_vec) == 1:
        return ajr[key]
    # if the key is nested than iterate to change
    else:
        curr_d = ajr
        for k in key_vec[:-1]:
            curr_d = curr_d[k]
        return curr_d[key_vec[-1]]

def edit_job_setting(name: str, key: str, value):
    """edit a given setting of the job. can change nested keys by separating dot, for example key=fs.attribute_support"""
    # load file
    with open(get_job_settings_path(name), "r") as f:
        ajr = yaml.safe_load(f)
    # change setting
    key_vec = key.split(".")
    if len(key_vec) == 1:
        ajr[key] = value
    # if the key is nested than iterate to change
    else:
        curr_d = ajr
        for k in key_vec[:-1]:
            curr_d = curr_d[k]
        curr_d[key_vec[-1]] = value
    # write change settings to file
    with open(get_job_settings_path(name), "w") as f:
        yaml.dump(ajr, f)
        print("Saved job settings to", get_job_settings_path(name), "changed", key, "to", value)

def run_job(name: str,model, target_dir: str):
    """Method to run a fscrawler job. note that it must be pre-configured to run. returns the process object"""
    # before anything we make sure that the job was created
    #get_job_settings_path(name)
    # now run the job
   
    start_time=time.time()
    zero_index_meta(name)
    #p = Popen(cmd, text=True)
    p=None
    def watcher(start_time=start_time):
        p=run_fs_docker_job(name,target_dir)
        fs_time=time.time()-start_time
        EsClient.indices.refresh(index=name)
        print(f"FS Crawler job {name} finished in {fs_time:.1f} seconds.")
        add_index_meta(name,fs_time,0,0)
        start_time=time.time()
        #Update_all_dwgs_dwgs(EsClient, name)
        dwg_time= time.time()-start_time
        add_index_meta(name, fs_time, dwg_time, 0)
        start_time=time.time()
        
        Update_all_semantics(EsClient, name, model)
        semantic_time= time.time()-start_time
        add_index_meta(name, fs_time, dwg_time, semantic_time)
    threading.Thread(target=watcher, daemon=True, args=(start_time,)).start()
    FSCRAWLER_JOBS[name] = p
    return p
def zero_index_meta(index_name:str):
    if not index_exists(EsClient, index_name):
        return
    EsClient.indices.put_mapping(
    index=index_name,
    _meta={        "fs_indexing_seconds":"0.0",
        "dwg_indexing_seconds": "0.0" ,
        "semantic_indexing_seconds": "0.0" 
    }
    )
def add_index_meta(index_name:str,fs_indexing_time:float,dwg_indexing_time:float,semantic_indexing_time:float):
    EsClient.indices.put_mapping(
    index=index_name,
    _meta={        "fs_indexing_seconds":f"{fs_indexing_time:.1f}",
        "dwg_indexing_seconds": f"{dwg_indexing_time:.1f}" ,
        "semantic_indexing_seconds": f"{semantic_indexing_time:.1f}" 
    }
    )
def stop_job(name: str):
    """Method to stop a running FSCrawler job"""
    if not name in FSCRAWLER_JOBS:
        raise FscrawlerError("Specified job doesn't exist")
    # if there is no process in the dictionary than the process is created and not started
    if FSCRAWLER_JOBS[name] is None:
        return 
    else:
        # else, use the Popen.kill method to kill the process
        FSCRAWLER_JOBS[name].terminate()


def jobs_status():
    """Method to return information on all existing jobs in json format"""
    jobs = []
    # {"name": "job1", "directory": "C:", "indexed_files": 30000, "status": "running"}
    for name in get_all_jobs():
        if not index_exists(EsClient, name):#found folder but no index
            status = "missing"
            job = {"name": name, "indexed_files": 0, "directory": get_job_setting(name, "fs.url"),
                   "status": status,
                   "fs_indexing_seconds": None,
                   "dwg_indexing_seconds": None,
                   "semantic_indexing_seconds": None
                   }
            jobs.append(job)
            continue
        info = EsClient.indices.get_mapping(index=name)
        if not name in info:
            status = "not started"
            job = {"name": name, "indexed_files": 0, "directory": get_job_setting(name, "fs.url"),
                   "status": status,
                   "fs_indexing_seconds": None,
                   "dwg_indexing_seconds": None,
                   "semantic_indexing_seconds": None
                   }
            jobs.append(job)
            continue
        if info[name]["mappings"]["_meta"].get("semantic_indexing_seconds", None) !="0.0":
            status = "completed"
        else:
            status = "indexing" #if index exists but no semantic indexing(last stage) time yet
        job = {"name": name, "indexed_files": EsClient.count(index=name)["count"], "directory": get_job_setting(name, "fs.url"),
               "status": status,
               "fs_indexing_seconds": info[name]["mappings"]["_meta"].get("fs_indexing_seconds", None),
               "dwg_indexing_seconds": info[name]["mappings"]["_meta"].get("dwg_indexing_seconds", None),
               "semantic_indexing_seconds": info[name]["mappings"]["_meta"].get("semantic_indexing_seconds", None)
               }
        jobs.append(job)
    return jobs

def delete_job(name: str):
    # remove index from elasticsearch
    if index_exists(EsClient, name):
        EsClient.delete_by_query(index=name, body={'query':{'match_all':{}}})
    print("Deleted index", name, "from elasticsearch")
    # remove folder
    shutil.rmtree(os.path.join(CONFIG["fscrawler"]["config_dir"], name))
    print("Deleted job folder for", os.path.join(CONFIG["fscrawler"]["config_dir"], name))
    print(f"FSCRAWLER_JOBS: {FSCRAWLER_JOBS}")
    return True
def create_job_templates(esclient, newname:str):
    """Method to create fscrawler templates in elasticsearch with a new name"""
    json_path = "fscrawler_templates.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    templates = data.get("component_templates", [])
    for tpl in templates:
        name = tpl["name"].replace("try1", newname)
        body = tpl["component_template"]

        print(f"Uploading component template: {name}")
        response=EsClient.cluster.put_component_template(        name=name, body=body)


        print(f" → Elasticsearch response: {response}")
def compose_up_es():
    os.environ["STACK_VERSION"] = CONFIG["docker_env"]["STACK_VERSION"]
    os.environ["LICENSE"] = CONFIG["docker_env"]["LICENSE"]
    os.environ["ES_PORT"] = CONFIG["docker_env"]["ES_PORT"]
    os.environ["CLUSTER_NAME"] = CONFIG["docker_env"]["CLUSTER_NAME"]
    os.environ["MEM_LIMIT"] = CONFIG["docker_env"]["MEM_LIMIT"]  
    os.environ["ES_PATH"] = os.path.abspath("..\\es_data")
    subprocess.run(["docker", "compose","-f", "crawler.yml" ,"up", "-d","es"], check=True)
if __name__ == "__main__":
    name="test"
    foldertoindex="C:\\install\\Pdfs\\try1"
    #foldertoindex="C:\\install\\Pdfs\\PHD_litreture"
    if not is_es_alive(EsClient):
        print("Elasticsearch is not reachable. Starting by docker compose...") 
        compose_up_es()
        wait_for_es(EsClient)
    create_job_templates(EsClient,name)
    create_new_job(name)
    #edit_job_setting(name, "fs.url", foldertoindex)
    edit_job_setting(name, "fs.ocr.enabled", False)
    edit_job_setting(name, "fs.ocr.data_path", "")
    edit_job_setting(name, "fs.ocr.path", "") 
   
    run_job("test",None,foldertoindex)
    sleep_time=600
    print(f"Sleeping main thread for {sleep_time} seconds to allow indexing to complete...")
    time.sleep(sleep_time)
