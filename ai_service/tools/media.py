from io import BytesIO
from typing import List

from PIL import Image
from PIL.ImageFile import ImageFile
from fastapi import UploadFile, File, APIRouter
from ultralytics import YOLO
from ultralytics.engine.results import Results

router = APIRouter()
yolov8n_model: YOLO = YOLO('yolov8n.pt')


@router.post("/yolov8n", summary="Returns a list of objects detected in the image using the YoloV8 Nano model.")
async def yolov8n(image: UploadFile = File(...)) -> List[str]:
    image_file: ImageFile = Image.open(BytesIO(await image.read()))
    prediction_results: List[Results] = yolov8n_model.predict(image_file, classes=[0, 2], verbose=False, device='cuda')
    detected_object_list: List[str] = list(map(lambda c: yolov8n_model.names[c], prediction_results[0].boxes.cls.tolist()))
    return detected_object_list
