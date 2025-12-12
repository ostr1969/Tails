from fastapi import FastAPI, File, UploadFile
import subprocess
import tempfile
import os

app = FastAPI()
#./DwgTextract Samples/2.dwg Extractor/Resources/encode_list.csv Extractor/Resources/Fonts

@app.post("/process")
async def process(file: UploadFile = File(...)):
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Run your Linux executable
    proc = subprocess.run(
        ["/app/DwgTextract", tmp_path,"Resources/encode_list.csv","Resources/Fonts"],
        capture_output=True,
        text=True
    )

    os.unlink(tmp_path)

    # Return stdout + stderr
    return {
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode
    }
