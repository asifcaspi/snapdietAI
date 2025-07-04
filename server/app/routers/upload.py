from collections import defaultdict
import io
import base64
import os
import csv
import time
from fastapi import APIRouter
from PIL import Image
from app.models.b64_image_model import Base64Image
import numpy as np
from app.utils.image_utils import calculate_amount_of_calories, convert_image_to_base64, get_pixel_size_in_mm, merge_segments_if_similar, remove_duplicate_segments_from_masks, show_segments_on_image
import torch
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Force TensorFlow to use CPU
import tensorflow as tf
import open_clip
import joblib
import platform
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

from app.constants.non_food import non_food
from app.constants.coins import coins_names

torch.set_num_threads(8)

coin_model_path = os.path.join(os.path.dirname(__file__), "../../coin_detection.keras")
if not os.path.exists(coin_model_path):
    url = "1_Nb8SS0mUhQc-ZSjbTHxCsqpjOP4QB8r"

    os.system(f"gdown {url} -O {coin_model_path}")

output_file = os.path.join(os.path.join(os.path.dirname(__file__), "../../sam_vit_l_0b3195.pth"))
if not os.path.exists(output_file):
    url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth"

    if platform.system() == "Windows":
        os.system(f"curl -o \"{output_file}\" {url}")
    else:
        os.system(f"wget -O \"{output_file}\" {url}")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
model = model.to(device).eval()

coin_detection_model = tf.keras.models.load_model(coin_model_path)
knn_clip = joblib.load(os.path.join(os.path.dirname(__file__), "../../knn_clip.pkl"))

sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to(device)
mask_generator = SamAutomaticMaskGenerator(sam, points_per_side=16)

router = APIRouter()

calories_path = os.path.join(os.path.dirname(__file__), "../../calories.csv")
with open(calories_path, "r") as f:
    reader = csv.DictReader(f)
    calories = {row["FoodItem"]: row["Cals_per100grams"] for row in reader}

def image_preprocess(img):
    image = img.copy()
    image = tf.image.resize(image, (224, 224))
    image = np.array(image)
    image = tf.keras.applications.resnet50.preprocess_input(image)
    return tf.expand_dims(image, 0)

def coin_detection(image):
    image = image_preprocess(image)
    preds = coin_detection_model.predict(image)
    idx = np.argmax(preds[0])
    conf = preds[0][idx]
    print(f"Coin detected class: {idx} → “{coins_names[idx]}”  (confidence: {conf:.3f})")

    return coins_names[idx], conf

def get_clip_embedding(image):
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        img_feat = model.encode_image(image_tensor)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
    return img_feat.cpu().numpy().flatten()

def clip_classification(image):
    image_embedding_clip = get_clip_embedding(image)
    clip_distances, clip_indices = knn_clip.kneighbors([image_embedding_clip], n_neighbors=1)
    clip_pred = knn_clip.predict([image_embedding_clip])[0]
    clip_dist = clip_distances[0][0]

    print(f"Clip predict: {clip_pred} with distance of: {clip_dist}")

    return clip_pred, clip_dist

def hybrid_classify(image):
    clip_pred, clip_dist = clip_classification(image)
    if clip_pred == "coin":
        coin_pred, coin_conf = coin_detection(image)
        return coin_pred, coin_conf
    elif clip_dist >= 0.71:
        return "unknown", clip_dist
    else:
        return clip_pred, clip_dist
    
# Segment and classify each segment + merging
def segment_and_classify(image):
    image = np.array(image)

    # Time measurement for SAM segmentation
    start_sam = time.time()
    masks = mask_generator.generate(image)
    end_sam = time.time()
    print(f"SAM prediction time: {end_sam - start_sam:.4f} seconds")

    # Sort masks by area (or use 'area' or 'stability_score')
    masks = sorted(masks, key=lambda x: np.sum(x["segmentation"]), reverse=True)

    # Removing overriding segments
    masks = remove_duplicate_segments_from_masks(masks)

    output = []

    coinIdx = None
    for mask_dict in masks:
        seg_mask = mask_dict["segmentation"]

        # Create masked segment image
        masked_image = image.copy()
        masked_image[~seg_mask] = 0

        pil_segment = Image.fromarray(masked_image)
        pred, conf = hybrid_classify(pil_segment)

        pixel_count = np.sum(seg_mask)
        x, y, z = image.shape
        minSize = (x * y) / 130

        obj = {
            "mask": seg_mask,
            "class": pred,
            "conf": conf,
            "pixels": pixel_count
        }

        if pred in coins_names:
            if coinIdx is None:
                print(f"Found the first coin segment no.{len(output)}")
                coinIdx = len(output)
            else:
                if conf > output[coinIdx]["conf"]:
                    print(f"Found better coin, replace segment no.{coinIdx}")
                    output[coinIdx] = obj
                else:
                    print(f"Ignoring the coin, better one found before")
                    continue

        if pixel_count < (minSize) and pred not in coins_names:
          print(f"Too small segment, ignoring")
          continue

        if pred == "unknown":
          print(f"Not a solid classification, ignoring")
          continue

        output.append(obj)

    print(f"Initial segments: {len(output)}, Merging segments")
    merged_output = merge_segments_if_similar(output, image)
    return merged_output

def image_class_list(segments):
    class_pixel_map = defaultdict(int)

    for seg in segments:
        class_name = seg["class"]
        pixel_count = seg["pixels"]
        class_pixel_map[class_name] += pixel_count

    result = [{"class": name, "pixels": pixels} for name, pixels in class_pixel_map.items() 
              if name not in non_food and name not in coins_names]
    return result

@router.post("/upload")
async def upload_image(data: Base64Image):
    image_data = base64.b64decode(data.image.split(",")[1])
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((512, 512))
    results = segment_and_classify(image)
    coin = [data for data in results if data["class"] in coins_names]
    class_list = image_class_list(results)
    if not len(coin):
        return {"error": "No coins detected"}
    pixel_mm = get_pixel_size_in_mm(coin[0]["pixels"], coin[0]["class"])
    result = {}
    for data in class_list:
        matching_calories = None
        for key, value in calories.items():
            if str(data["class"]).lower() in key.lower():
                matching_calories = value
                break  # Stop searching after the first match
        result[str(data["class"])] = calculate_amount_of_calories(pixel_mm, data["pixels"], float(matching_calories.removesuffix(" cal"))) if matching_calories else None
    
    
    return { "result": result, "image": convert_image_to_base64(show_segments_on_image(image, results)) }


