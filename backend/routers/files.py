from fastapi import APIRouter, Security, File, UploadFile
from auth0.utils import VerifyToken
import os
from pathlib import Path

auth = VerifyToken()

# Storage directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok = True)

router = APIRouter(prefix="/file", tags=["File"])

@router.post("/upload")
async def upload_file(files: list[UploadFile] = File(...), security: dict[str, str] = Security(auth.verify)):
    ## Get unique user id from teh subject id in the authentication token
    user_id = security["sub"].split("@")[0]
    user_dir = Path(UPLOAD_DIR) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_data = dict()
    for file in files:
        if file.filename is not None:
            file_path = user_dir / file.filename
            with file_path.open("wb") as f:
                f.write(await file.read())
                file_data[file.filename] = file.size

    return file_data

@router.get("/list_files")
def get_files(security: dict[str, str] = Security(auth.verify)):
    user_id = security["sub"].split("@")[0]
    user_dir = Path(UPLOAD_DIR) / user_id
    files = os.listdir(user_dir)

    return files
