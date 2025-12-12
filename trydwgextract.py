import json
import requests

def run_process(file_path: str):
    url = "http://localhost:4100/process"

    with open(file_path, "rb") as f:
        response = requests.post(url, files={"file": f})

    response.raise_for_status()

    data = response.json()          # the API’s JSON
    stdout_text = data["stdout"]    # this is a long text
    stdout_json = json.loads(stdout_text)  # parse it as JSON

    return stdout_json
if __name__ == "__main__":
    result = run_process("Samples/try1/e1.dwg")
    print(json.dumps(result, indent=2))