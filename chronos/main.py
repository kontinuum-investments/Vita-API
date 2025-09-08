import asyncio
from contextlib import asynccontextmanager
from enum import Enum
from typing import List, AsyncGenerator, Any

import cv2
from apscheduler.events import EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sirius import common
from sirius.http_requests import AsyncHTTPSession, HTTPResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response


class Job(Enum):
    CHECK_BACKYARD_CAMERA = "CHECK_BACKYARD_CAMERA"
    CHECK_LEFT_CORRIDOR_CAMERA = "CHECK_LEFT_CORRIDOR_CAMERA"
    CHECK_GARAGE_CAMERA = "CHECK_GARAGE_CAMERA"
    CHECK_FRONT_CAMERA = "CHECK_FRONT_CAMERA"


def log_job_duration(event: JobExecutionEvent) -> None:
    # time_now = datetime.datetime.now(datetime.timezone.utc).astimezone(event.scheduled_run_time.tzinfo)
    # job_runtime = (time_now - event.scheduled_run_time).total_seconds() * 1000
    # print(f"Job '{event.job_id}' took {job_runtime:.2f}ms to complete.")
    pass


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> None:
    if not common.is_production_environment():
        return

    if token.credentials != common.get_environmental_secret("API_KEY"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, )


scheduler = AsyncIOScheduler()
scheduler.add_listener(log_job_duration, EVENT_JOB_EXECUTED)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    scheduler.add_job(analyze_camera, IntervalTrigger(seconds=5), args=[common.get_environmental_secret("RTSP_URL_FRONT_CAMERA")], max_instances=3, id=Job.CHECK_FRONT_CAMERA.value)
    # scheduler.add_job(analyze_camera, IntervalTrigger(seconds=5), args=[common.get_environmental_secret("RTSP_URL_BACKYARD_CAMERA")], max_instances=3, id=Job.CHECK_BACKYARD_CAMERA.value)
    # scheduler.add_job(analyze_camera, IntervalTrigger(seconds=5), args=[common.get_environmental_secret("RTSP_URL_GARAGE_CAMERA")], max_instances=3, id=Job.CHECK_GARAGE_CAMERA.value)
    # scheduler.add_job(analyze_camera, IntervalTrigger(seconds=5), args=[common.get_environmental_secret("RTSP_URL_LEFT_CORRIDOR_CAMERA")], max_instances=3, id=Job.CHECK_LEFT_CORRIDOR_CAMERA.value)
    scheduler.start()

    yield

    scheduler.shutdown()


chronos_app = FastAPI(lifespan=lifespan)
chronos_app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@chronos_app.get("/ping", summary="Returns a 200 response code by default. Used to check if the service is alive.")
async def ping() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@chronos_app.post("/analyze_camera", summary="Looks are the camera that's from the RTSP URL. A message will be sent on Discord on anything suspicious.")
async def analyze_camera(video_stream_address: str) -> Response:
    def get_latest_camera_frame(url: str) -> bytes | None:
        successful_frame_read, frame = cv2.VideoCapture(url).read()
        if not successful_frame_read:
            return None

        successful_encoding, encoded_frame = cv2.imencode('.jpg', frame)
        return encoded_frame.tobytes()

    latest_frame: bytes = await asyncio.to_thread(get_latest_camera_frame, video_stream_address)
    if not latest_frame:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    apollo_url: str = f"{common.get_environmental_secret("APOLLO_BASE_URL")}/media/object_detection"
    response: HTTPResponse = await AsyncHTTPSession(apollo_url).post(apollo_url, files={'image': ('image.jpeg', latest_frame, 'image/jpeg')}, headers={"Authorization": f"Bearer {common.get_environmental_secret("API_KEY")}"})
    object_list: List[str] = [data["description"] for data in response.data]

    for object in object_list:
        discord_url: str = f"{common.get_environmental_secret("APOLLO_BASE_URL")}/discord/send_message"
        await AsyncHTTPSession(discord_url).post(discord_url, data={"message": f"{str(object).title()} detected in the front camera."}, headers={"Authorization": f"Bearer {common.get_environmental_secret("API_KEY")}"})

    return Response(status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:chronos_app", host="0.0.0.0", port=8003, reload=True)
