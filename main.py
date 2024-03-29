import asyncio
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sirius import common
from sirius.communication.logger import Logger
from sirius.exceptions import SiriusException
from sirius.scheduler import AsynchronousScheduler
from starlette.responses import JSONResponse

from api import constants
from api.ares.router import ares_router
from api.athena.router import athena_router
from api.athena.services.discord import Discord
from api.chronos.router import chronos_router
from api.exceptions import ClientException
from api.hades.router import hades_router
from api.hades.services.monthly_financial_organisation import MonthlyFinances
from api.hades.services.transaction_organisation import WiseDebitEvent
from api.hermes.router import hermes_router


@asynccontextmanager
async def lifespan(fast_api_app: FastAPI) -> AsyncGenerator:
    asyncio.ensure_future(schedule_jobs())
    asyncio.ensure_future(Logger.debug("Vita API started up successfully"))
    Discord.start_discord_client()
    yield


app = FastAPI(
    title="Vita API",
    description="API for Personal Automation",
    lifespan=lifespan
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


async def schedule_jobs() -> None:
    await AsynchronousScheduler.add_job(func=WiseDebitEvent.organise_transactions, minute=00)

    await AsynchronousScheduler.add_job(func=MonthlyFinances.do, day=28, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do, day=29, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do, day=30, hour=23, minute=30, second=0)
    await AsynchronousScheduler.add_job(func=MonthlyFinances.do, day=31, hour=23, minute=30, second=0)


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


if __name__ == "__main__":
    if not common.is_production_environment() and sys.gettrace() is not None:
        import pydevd_pycharm

        pydevd_pycharm.settrace('127.0.0.1', port=constants.DEBUG_PORT_NUMBER, stdoutToServer=True, stderrToServer=True)

    uvicorn.run("main:app", log_level="debug", reload=common.is_development_environment(), port=constants.PORT_NUMBER)
