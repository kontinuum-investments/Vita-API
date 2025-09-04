import base64
from io import BytesIO
from typing import List

from PIL import Image
from fastapi import UploadFile, File, APIRouter
from sirius.common import DataClass
from ultralytics import YOLO
from ultralytics.engine.results import Results
import torch

router = APIRouter()
yolov8n_model: YOLO = YOLO('yolov8n.pt')


class ObjectDetectionResponse(DataClass):
    description: str
    image_base64: str


@router.post("/object_detection", summary="Detects objects in the image and returns a list of cropped images of the detected objects.")
async def object_detection(image: UploadFile = File(...)) -> List[ObjectDetectionResponse]:
    image_bytes = await image.read()
    image_file: Image.Image = Image.open(BytesIO(image_bytes))
    raw_prediction_results: List[Results] = yolov8n_model.predict(image_file, classes=[0, 2], verbose=False, device= "cuda" if torch.cuda.is_available() else "cpu")
    prediction_results: List[ObjectDetectionResponse] = []

    for box in [box for detections in raw_prediction_results for box in detections.boxes]:  # type: ignore[attr-defined]
        class_id = int(box.cls.tolist()[0])
        object_name = yolov8n_model.names[class_id]
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cropped_image = image_file.crop((x1, y1, x2, y2))
        cropped_image_bytes_io = BytesIO()
        cropped_image.save(cropped_image_bytes_io, format='JPEG')
        cropped_image_bytes = cropped_image_bytes_io.getvalue()

        prediction_results.append(ObjectDetectionResponse(description=object_name, image_base64=base64.b64encode(cropped_image_bytes).decode("ascii")))

    return prediction_results
