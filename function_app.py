import azure.functions as func
from fastapi import FastAPI, Request, Response

fast_app = FastAPI()


@fast_app.function_name(name="API")
@fast_app.get("/return_http_no_body")
async def return_http_no_body():
    return Response(content="Kavindu is handsome", media_type="text/plain")


app = func.AsgiFunctionApp(app=fast_app,
                           http_auth_level=func.AuthLevel.ANONYMOUS)
