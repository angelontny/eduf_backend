from fastapi import APIRouter, Security, File, UploadFile, HTTPException
from auth0.utils import VerifyToken
from fastapi.responses import FileResponse
import os
from pathlib import Path

auth = VerifyToken()

# Storage directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok = True)

router = APIRouter(prefix="/file", tags=["File"])

@router.post("/upload/{chat_id}")
async def upload_file(chat_id: int, files: list[UploadFile] = File(...), security: dict[str, str] = Security(auth.verify)):
    ## Get unique user id from the subject id in the authentication token
    user_id = security["sub"].split("@")[0]
    user_dir = Path(UPLOAD_DIR) / user_id / str(chat_id)

    user_dir.mkdir(parents=True, exist_ok=True)
    
    file_data = dict()
    for file in files:
        if file.filename is not None:
            file_path = user_dir / file.filename
            with file_path.open("wb") as f:
                f.write(await file.read())
                file_data[file.filename] = file.size

    return file_data

@router.get("/list_files/{chat_id}")
def get_files(chat_id: int, security: dict[str, str] = Security(auth.verify)):
    user_id = security["sub"].split("@")[0]
    user_dir = Path(UPLOAD_DIR) / user_id / str(chat_id)
    try:
        files = os.listdir(user_dir)
    except:
        raise HTTPException(status_code=404, detail="Chat not found")

    return files

@router.get("/fetch_file/{chat_id}/{file_name}")
def fetch_file(chat_id: str, file_name: str, security: dict[str, str] = Security(auth.verify)):
    user_id = security["sub"].split("@")[0]
    file_path = Path(UPLOAD_DIR) / user_id / chat_id / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)

