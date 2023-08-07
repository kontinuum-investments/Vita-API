import azure.functions as func
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from api.ares.router import ares_router
from api.athena.router import athena_router
from api.chronos.router import chronos_router
from api.hades.router import hades_router
from api.hermes.router import hermes_router

fast_app = FastAPI()
fast_app.include_router(ares_router)
fast_app.include_router(athena_router)
fast_app.include_router(chronos_router)
fast_app.include_router(hades_router)
fast_app.include_router(hermes_router)


@fast_app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


app = func.AsgiFunctionApp(app=fast_app, http_auth_level=func.AuthLevel.ANONYMOUS)
