import asyncio
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sirius import common
from sirius.communication.logger import Logger
from sirius.exceptions import SiriusException
from sirius.scheduler import AsynchronousScheduler
from starlette.responses import JSONResponse, StreamingResponse

from api import constants
from api.ares.models.database import HTTPExchange
from api.ares.router import ares_router
from api.athena.router import athena_router
from api.chronos.router import chronos_router
from api.exceptions import ClientException
from api.hades.router import hades_router
from api.hades.services.organize_daily_finances import DailyFinances
from api.hades.services.organize_monthly_finances import MonthlyFinances
from api.hades.services.organize_rent import OrganizeRent
from api.hermes.router import hermes_router

app = FastAPI(
    title="Vita API",
    description="API for Personal Automation"
)
app.include_router(ares_router, tags=["Ares"])
app.include_router(athena_router, tags=["Athena"])
app.include_router(chronos_router, tags=["Chronos"])
app.include_router(hades_router, tags=["Hades"])
app.include_router(hermes_router, tags=["Hermes"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.on_event("startup")
async def start_up() -> None:
    asyncio.ensure_future(schedule_jobs())
    asyncio.ensure_future(Logger.debug("Vita API started up successfully"))


async def schedule_jobs() -> None:
    await AsynchronousScheduler.add_job(func=DailyFinances.do, hour=0, minute=0, second=0)
    await AsynchronousScheduler.add_job(func=OrganizeRent.do, day_of_week="thu", hour=15, minute=0, second=0)

    await AsynchronousScheduler.add_job(func=MonthlyFinances.do_organize_finances_for_at_start_of_month, day=28, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do_organize_finances_for_at_start_of_month, day=29, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do_organize_finances_for_at_start_of_month, day=30, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do_organize_finances_for_at_start_of_month, day=31, hour=23, minute=30, second=0)


@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    await Logger.debug(str(exception))
    return JSONResponse(
        status_code=400 if isinstance(exception, (ClientException, SiriusException)) else 500,
        content={"message": f"{str(exception)}"},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    response: StreamingResponse = await call_next(request)
    await HTTPExchange.log_request(request, response)
    return StreamingResponse(content=response.body_iterator, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)


if __name__ == "__main__":
    if not common.is_production_environment():
        import pydevd_pycharm

        pydevd_pycharm.settrace('127.0.0.1', port=constants.DEBUG_PORT_NUMBER, stdoutToServer=True, stderrToServer=True)

    uvicorn.run("main:app", log_level="debug", reload=common.is_development_environment(), port=constants.PORT_NUMBER)
