from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sirius import common
from starlette.middleware.cors import CORSMiddleware

from tools import discord, ibkr, wise


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> None:
    api_key: str = common.get_environmental_secret("API_KEY")
    if token.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(discord.router, prefix="/discord", dependencies=[Depends(verify_token)])
app.include_router(ibkr.router, prefix="/ibkr", dependencies=[Depends(verify_token)])
app.include_router(wise.router, prefix="/wise", dependencies=[Depends(verify_token)])

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
