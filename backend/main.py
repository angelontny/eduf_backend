from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

token_auth_scheme = HTTPBearer()
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
def private(token: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
    """A valid access token is required to access this route"""

    result = token.credentials

    return result
