from fastapi import Security, FastAPI
from auth0.utils import VerifyToken

auth = VerifyToken()
app = FastAPI()

@app.get("/api/public")
def public():
    result = {
        "status": "success",
        "msg": ("Hello from a public endpoint! You don't need to be "
                "authenticated to see this.")
    }
    return result

@app.get("/api/private")
def private(auth_string: str = Security(auth.verify)):
    """A valid access token is required to access this route"""

    result = auth_string

    return result
