from fastapi import Security, FastAPI
from auth0.utils import VerifyToken
from routers import files, chats, rag

auth = VerifyToken()
app = FastAPI()
app.include_router(files.router)
app.include_router(chats.router)
app.include_router(rag.router)

