from collections import defaultdict
import io
import base64
import os
import csv
from fastapi import APIRouter
from PIL import Image
from app.models.b64_image_model import Base64Image
import numpy as np
# import tensorflow as tf
from app.utils.image_utils import calculate_amount_of_calories, get_pixel_size_in_mm
import torch
import open_clip
import joblib
import platform
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

torch.set_num_threads(8)

output_file = os.path.join(os.path.join(os.path.dirname(__file__), "../../sam_vit_h_4b8939.pth"))
if not os.path.exists(output_file):
    url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"

    if platform.system() == "Windows":
        os.system(f"curl -o \"{output_file}\" {url}")
    else:
        os.system(f"wget -O \"{output_file}\" {url}")

device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
model = model.to(device).eval()

knn = joblib.load(os.path.join(os.path.dirname(__file__), "../../knn_model.joblib"))

sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
sam.to(device)
mask_generator = SamAutomaticMaskGenerator(sam, points_per_side=16, min_mask_region_area=100)

router = APIRouter()

calories_path = os.path.join(os.path.dirname(__file__), "../../calories.csv")
with open(calories_path, "r") as f:
    reader = csv.DictReader(f)
    calories = {row["FoodItem"]: row["Cals_per100grams"] for row in reader}

# category_id_path = os.path.join(os.path.dirname(__file__), "../../category_id.txt")
# with open(category_id_path, "r") as f:
#     category_reader = csv.reader(f, delimiter="\t")
#     class_from_id = {int(row[0]): row[1] for row in category_reader}

def classify_segment(image):
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        img_feat = model.encode_image(image_tensor)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
    distances, indices = knn.kneighbors([img_feat.cpu().numpy().flatten()])
    confidence = 1 - distances.ravel() 
    return knn.predict([img_feat.cpu().numpy().flatten()])[0], confidence[0]

# Segment and classify each segment
def segment_and_classify(image_object, max_segments=10):
    image = np.array(image_object)

    # Generate all masks
    masks = mask_generator.generate(image)

    # Sort masks by area (or use 'area' or 'stability_score')
    masks = sorted(masks, key=lambda x: np.sum(x["segmentation"]), reverse=True)

    # Take only the top-N masks
    masks = masks[:max_segments]

    print(f'Using top {len(masks)} segments')

    output = []
    for idx, mask_dict in enumerate(masks):
        seg_mask = mask_dict["segmentation"]

        # Create masked segment image
        masked_image = image.copy()
        masked_image[~seg_mask] = 0

        pil_segment = Image.fromarray(masked_image)
        class_name, confidence = classify_segment(pil_segment)
        pixel_count = np.sum(seg_mask)
        if confidence > 0.25:
            output.append({
                "mask": seg_mask,
                "class": class_name,
                "pixels": pixel_count
            })

    return output

def image_class_list(segments):
    class_pixel_map = defaultdict(int)

    for seg in segments:
        class_name = seg["class"]
        pixel_count = seg["pixels"]
        class_pixel_map[class_name] += pixel_count

    result = [{"class": name, "pixels": pixels} for name, pixels in class_pixel_map.items()]
    return result

## For local use only
# import psutil
# p = psutil.Process(os.getpid())

# # Limit the process to specific CPU cores (e.g., cores 0 and 1)
# p.cpu_affinity([0, 1])

@router.post("/upload")
async def upload_image(data: Base64Image):
    image_data = base64.b64decode(data.image.split(",")[1])
    image = Image.open(io.BytesIO(image_data))
    original_width, _ = image.size
    pixel_mm = get_pixel_size_in_mm(image)
    image = image.resize((224, 224))
    pixel_mm = (original_width / 224) * pixel_mm
    results = segment_and_classify(image)
    class_list = image_class_list(results)
    result = {}
    for data in class_list:
        matching_calories = None
        for key, value in calories.items():
            if str(data["class"]).lower() in key.lower():
                matching_calories = value
                break  # Stop searching after the first match
        result[str(data["class"])] = calculate_amount_of_calories(pixel_mm, data["pixels"], float(matching_calories.removesuffix(" cal")))
    return result


