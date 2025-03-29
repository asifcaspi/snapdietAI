import io
import base64
import os
from csv import DictReader
from fastapi import APIRouter, HTTPException
from PIL import Image
from app.models.b64_image_model import Base64Image
from ultralytics import YOLO

router = APIRouter()
model_path = os.path.join(os.path.dirname(__file__), "../../best.pt")
model = YOLO(model_path)

calories_path = os.path.join(os.path.dirname(__file__), "../../calories.csv")
with open(calories_path, "r") as f:
    reader = DictReader(f)
    calories = {row["FoodItem"]: row["Cals_per100grams"] for row in reader}

@router.post("/upload")
async def upload_image(data: Base64Image):
    try:
        image_data = base64.b64decode(data.image.split(",")[1])
        image = Image.open(io.BytesIO(image_data))
        model_results = model.predict(image, conf=0.5, verbose=True)
        result = {}
        for model_result in model_results:
            for class_id in model_result.boxes.cls:
                class_name = model_result.names[int(class_id)]
                matching_calories = None
                for key, value in calories.items():
                    if class_name in key:
                        matching_calories = value
                        break  # Stop searching after the first match
                result[class_name] = matching_calories
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")