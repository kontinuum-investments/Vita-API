import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sirius import common
from sirius.communication.logger import Logger
from sirius.scheduler import AsynchronousScheduler
from starlette.responses import JSONResponse

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
app.include_router(ares_router)
app.include_router(athena_router)
app.include_router(chronos_router)
app.include_router(hades_router)
app.include_router(hermes_router)


@app.on_event("startup")
async def start_up() -> None:
    await schedule_jobs()
    await Logger.debug("Vita API started up successfully")


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


# TODO: Does not work; handles even caught exceptions
@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=400 if isinstance(exception, ClientException) else 500,
        content={"message": f"{str(exception)}"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=80 if common.is_development_environment() else 443, log_level="debug")
