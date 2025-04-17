import io
import base64
import os
import csv
from fastapi import APIRouter
from PIL import Image
from app.models.b64_image_model import Base64Image
import numpy as np
import tensorflow as tf
from app.utils.image_utils import get_pixel_size_in_mm

router = APIRouter()
model_path = os.path.join(os.path.dirname(__file__), "../../model.keras")
model = tf.keras.models.load_model(model_path)

calories_path = os.path.join(os.path.dirname(__file__), "../../calories.csv")
with open(calories_path, "r") as f:
    reader = csv.DictReader(f)
    calories = {row["FoodItem"]: row["Cals_per100grams"] for row in reader}

category_id_path = os.path.join(os.path.dirname(__file__), "../../category_id.txt")
with open(category_id_path, "r") as f:
    category_reader = csv.reader(f, delimiter="\t")
    class_from_id = {int(row[0]): row[1] for row in category_reader}

@router.post("/upload")
async def upload_image(data: Base64Image):
    image_data = base64.b64decode(data.image.split(",")[1])
    image = Image.open(io.BytesIO(image_data))
    pixel_mm = get_pixel_size_in_mm(image)
    resized_image = image.resize((224, 224))
    model_results = model.predict(np.expand_dims(resized_image, axis=0))
    model_result_classes = np.argmax(model_results, axis=-1)
    pred_conf = np.max(model_results, axis=-1)

    # Suppress low-confidence predictions
    model_result_classes[pred_conf < 0.5] = 0
    unique_classes = np.unique(model_result_classes).tolist()
    unique_classes.remove(0)
    temp = Image.fromarray(model_result_classes[0].astype(np.uint8))
    temp.show()
    result = {}
    for class_id in unique_classes:
        class_name = class_from_id[class_id]
        matching_calories = None
        for key, value in calories.items():
            if class_name in key:
                matching_calories = value
                break  # Stop searching after the first match
        result[class_name] = matching_calories
    return result
