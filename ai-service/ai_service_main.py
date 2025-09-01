from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sirius import common
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response


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

@app.get("/ping", summary="Returns a 200 response code by default. Used to check if the service is alive.")
async def ping() -> Response:
    return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
