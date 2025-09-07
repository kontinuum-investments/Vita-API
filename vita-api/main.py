from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sirius import common
from starlette.middleware.cors import CORSMiddleware

from tools import discord, ibkr, wise


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> None:
    if not common.is_production_environment():
        return

    if token.credentials != common.get_environmental_secret("API_KEY"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, )


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(discord.router, prefix="/discord", dependencies=[Depends(verify_token)])
app.include_router(ibkr.router, prefix="/ibkr", dependencies=[Depends(verify_token)])
app.include_router(wise.router, prefix="/wise", dependencies=[Depends(verify_token)])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
