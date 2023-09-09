import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sirius.scheduler import AsynchronousScheduler
from starlette.responses import JSONResponse

from api.ares.router import ares_router
from api.athena.router import athena_router
from api.chronos.router import chronos_router
from api.exceptions import ClientException
from api.hades.router import hades_router
from api.hades.services.organize_daily_finances import DailyFinances
from api.hermes.router import hermes_router

app = FastAPI(
    title="Vita API",
    description="API for Personal Automation"
)
app.include_router(ares_router)
app.include_router(athena_router)
app.include_router(chronos_router)
app.include_router(hades_router)
app.include_router(hermes_router)


@app.on_event("startup")
async def schedule_jobs() -> None:
    await AsynchronousScheduler.add_job(func=DailyFinances.do, hour=0, minute=0, second=0)


@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


# TODO: Does not work; handles even caught exceptions
@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=400 if isinstance(exception, ClientException) else 500,
        content={"message": f"{str(exception)}"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=443, log_level="debug")
