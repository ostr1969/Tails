# this file contains a module for using fscrawler from python
from __init__ import CONFIG, EsClient
import os
import shutil
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE
import yaml

FSCRAWLER_JOBS = {}

def get_all_jobs():
    """get all jobs of fscrawler"""
    jobs = []
    base_path = CONFIG["fscrawler"]["config_dir"]
    print(base_path)
    for obj in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, obj)) and not obj == "_default":
            jobs.append(obj)
    return jobs

def create_new_job(name: str):
    """create a new project for FSCrawler. this is the first step in running it."""
 
    exe_path = CONFIG["fscrawler"]["exe"]
    config_dir = CONFIG["fscrawler"]["config_dir"]
    current_config_dir=os.path.join(config_dir,name)
    print(current_config_dir)
    if name in FSCRAWLER_JOBS and os.path.isdir(current_config_dir):
        return False
    # we create a job in the specified directory. also, we make sure the crawler will run only once on all files
    cmd = [exe_path, name, "--config_dir", config_dir, "--loop 1"]
    # run the process, we have to approve the creation by sending "yes"
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True, shell=True)
    proc.communicate("y\n")
    proc.wait()
    FSCRAWLER_JOBS[name] = None
    return True

class FscrawlerError (Exception):
    pass

def get_job_settings_path(name: str):
    path = os.path.join(CONFIG["fscrawler"]["config_dir"], name, "_settings.yaml")
    if not os.path.isfile(path):
        raise FscrawlerError("Specified project name doesn't exist,"+ 
                             "make sure to create it befor editing and running:\n"+
                             path)
    return path 

def load_defaults_to_job(name: str):
    """Method to load the default settings to a fscrawler job. they are defined in the CONFIG json"""
    # loading everything from the defaults file
    with open(CONFIG["fscrawler"]["defaults"], "r") as f:
        d = yaml.safe_load(f)
    # changing elasticsearch adress to the one in CONFIG
    d["elasticsearch"]["nodes"][0]["url"] = CONFIG["elasticsearch_url"]
    # setting name to proper name
    d["name"] = name
    # dumping settings to project dir
    jobDir=os.path.join(CONFIG["fscrawler"]["config_dir"], name)
    settingDir=os.path.join(CONFIG["fscrawler"]["config_dir"], name,"_settings.yaml")
    os.mkdir(jobDir)
    with open(settingDir, "w") as f:
        yaml.dump(d, f)

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

def run_job(name: str):
    """Method to run a fscrawler job. note that it must be pre-configured to run. returns the process object"""
    # before anything we make sure that the job was created
    get_job_settings_path(name)
    # now run the job
    exe_path = CONFIG["fscrawler"]["exe"]
    config_dir = CONFIG["fscrawler"]["config_dir"]
    # we create a job in the specified directory. also, we make sure the crawler will run only once on all files
    cmd = [exe_path, name, "--config_dir", config_dir, "--loop", "1"]
    # run the process, we have to approve the creation by sending "yes"
    p = Popen(cmd, text=True)
    FSCRAWLER_JOBS[name] = p
    return p

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
        job = {"name": name, "indexed_files": EsClient.count(index=name)["count"], "directory": get_job_setting(name, "fs.url")}
        jobs.append(job)
    return jobs

def delete_job(name: str):
    # remove index from elasticsearch
    EsClient.delete_by_query(index=name, body={'query':{'match_all':{}}})
    # remove folder
    shutil.rmtree(os.path.join(CONFIG["fscrawler"]["config_dir"], name))
    return True

    


