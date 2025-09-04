from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sirius import common
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> None:
    if not common.is_production_environment():
        return

    if token.credentials != common.get_environmental_secret("API_KEY"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, )


new_service_app = FastAPI()
new_service_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@new_service_app.get("/ping", summary="Returns a 200 response code by default. Used to check if the service is alive.")
async def ping() -> Response:
    return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    #   TODO: Set the port number
    uvicorn.run("main:new_service_app", host="0.0.0.0", port=8000, reload = True)
