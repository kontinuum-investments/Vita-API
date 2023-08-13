import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from api.ares.router import ares_router
from api.athena.router import athena_router
from api.chronos.router import chronos_router
from api.hades.router import hades_router
from api.hermes.router import hermes_router

app = FastAPI()
app.include_router(ares_router)
app.include_router(athena_router)
app.include_router(chronos_router)
app.include_router(hades_router)
app.include_router(hermes_router)


@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    uvicorn.run("main:app", port=443, log_level="debug")
