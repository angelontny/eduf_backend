from fastapi import APIRouter, Security
from auth0.utils import VerifyToken

auth = VerifyToken()

router = APIRouter(prefix="/file", tags=["File"])

@router.get("/file_list")
def print_file_list(security : dict[str, str] = Security(auth.verify)):
    return security["sub"]
