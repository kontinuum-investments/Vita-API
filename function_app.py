import datetime
import logging

import azure.functions as func
from fastapi import FastAPI, Response

from api.hades.router import hades_router

fast_app = FastAPI()
fast_app.include_router(hades_router)


@fast_app.get("/return_http_no_body")
async def return_http_no_body():
    return Response(content="Kavindu is handsome", media_type="text/plain")


app = func.AsgiFunctionApp(app=fast_app, http_auth_level=func.AuthLevel.ANONYMOUS)


@app.function_name(name="test_timer")
@app.schedule(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=True)
def test_function(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    if mytimer.past_due:
        logging.info('The timer is past due!')
    logging.info('Python timer trigger function ran at %s', utc_timestamp)
