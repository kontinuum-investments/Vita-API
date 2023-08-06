import azure.functions as func
from fastapi import FastAPI

from api.ares.router import ares_router
from api.athena.router import athena_router
from api.chronos.router import chronos_router
from api.hades.router import hades_router
from api.hades.services import DailyFinances
from api.hermes.router import hermes_router

fast_app = FastAPI()
fast_app.include_router(ares_router)
fast_app.include_router(athena_router)
fast_app.include_router(chronos_router)
fast_app.include_router(hades_router)
fast_app.include_router(hermes_router)

app = func.AsgiFunctionApp(app=fast_app, http_auth_level=func.AuthLevel.ANONYMOUS)


@app.function_name(name="organize_daily_finances")
@app.schedule(schedule="0 0 12 * * *", arg_name="mytimer")
async def organize_daily_finances(mytimer: func.TimerRequest) -> None:
    await DailyFinances.do()
