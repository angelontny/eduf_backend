from fastapi import Security, FastAPI
from auth0.utils import VerifyToken
from routers import files

auth = VerifyToken()
app = FastAPI()
app.include_router(files.router)

@app.get("/api/public")
def public():
    result = {
        "status": "success",
        "msg": ("Hello from a public endpoint! You don't need to be "
                "authenticated to see this.")
    }
    return result

@app.get("/api/private")
def private(auth_string: dict[str, str] = Security(auth.verify)):
    """A valid access token is required to access this route"""


    return auth_string["sub"]
