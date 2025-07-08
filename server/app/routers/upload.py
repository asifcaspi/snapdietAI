from collections import defaultdict
import io
import base64
import os
import time
from fastapi import APIRouter
from PIL import Image
from app.models.b64_image_model import Base64Image
import numpy as np
from app.utils.image_utils import (
    calculate_amount_of_calories,
    convert_image_to_base64,
    get_pixel_size_in_mm,
    merge_segments_if_similar,
    remove_duplicate_segments_from_masks,
    show_segments_on_image,
    bbox_segment,
    expand_mask,
)
from app.utils.general_utils import clean_results, merge_objects
import torch

from app.constants.calories import calories

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Force TensorFlow to use CPU

from app.constants.non_food import non_food
from app.constants.coins import coins_names
from app.ai_models.classifier import Classifier
from app.ai_models.sam import mask_generator
from app.ai_models.coin_detector import CoinDetector
from app.ai_models.blip import Blip

torch.set_num_threads(8)

classifier = Classifier()
coin_detector = CoinDetector()
blip = Blip()


# Segment and classify each segment + merging
def segment_and_classify(
    pil,
    knn_weight_threshold=1.45,
    knn_raw_threshold=0.68,
    prompt_threshold=0.27,
    prompt_threshold_fault=0.02,
    top_k=5,
):
    image = np.array(pil)

    prompts = ["Name all ingredients and prepared dishes you see in this photo."]
    start_cap = time.time()
    caption = blip.generate_caption(pil, prompts)
    results = merge_objects(caption)
    end_cap = time.time()
    print(f"BLIP prediction time: {end_cap - start_cap:.4f} seconds")

    # for BLIP-Base usage, remove where value contains a prompt
    results = clean_results(results)

    print(f"BLIP found: {results}")

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
    H, W, _ = image.shape
    minSize = (H * W) / 130

    # Pre-allocate blank canvas once
    blank = np.zeros_like(image)

    for mask_dict in masks:
        seg_mask = mask_dict["segmentation"]
        pixel_count = seg_mask.sum()
        print(f"Segment size: {pixel_count}px")

        # Create masked segment image
        masked_np = blank.copy()
        masked_np[seg_mask] = image[seg_mask]
        pil_segment = Image.fromarray(masked_np)

        pred, knn_res, ens_res = classifier.hybrid_classify(
            pil_segment,
            knn_weight_threshold,
            knn_raw_threshold,
            prompt_threshold,
            prompt_threshold_fault,
        )
        coin_conf = None
        if pred == "coin":
            pred, coin_conf = coin_detector.coin_detection(pil)

        obj = {
            "mask": seg_mask,
            "class": pred,
            "coin_conf": coin_conf,
            "pixels": pixel_count,
        }

        if obj["class"] in coins_names:
            if coinIdx is None:
                print(f"Found the first coin segment no.{len(output)}")
                coinIdx = len(output)
            else:
                old_coin_conf = output[coinIdx]["coin_conf"]
                print(
                    f"Found another coin, old coin conf - {old_coin_conf}, new coin conf - {coin_conf}"
                )
                if coin_conf > old_coin_conf:
                    print(f"Found better coin, replace segment no.{coinIdx}")
                    output[coinIdx] = obj
                else:
                    print("Ignoring weaker coin")

                continue

        if obj["pixels"] < (minSize) and obj["class"] not in coins_names:
            print("Too small segment, ignoring")
            continue

        if top_k < 1 or top_k > 10:
            top_k = 3

        if obj["class"] == "unknown":
            top_k_knn = [lbl for lbl, _, _ in knn_res[:top_k]]
            top_k_ens = [lbl for lbl, _ in ens_res[:top_k]]

            # find labels in both predictions
            common_candidates = set(top_k_knn).intersection(top_k_ens)
            rescued = False

            for candidate in common_candidates:
                if any(candidate in food or food in candidate for food in results):
                    obj["class"] = candidate
                    print(
                        f"Recovered '{candidate}' from top-{top_k} via substring match"
                    )
                    rescued = True
                    break

            if not rescued:
                print(
                    f"No shared candidate in top-{top_k} KNN & ENS for this segment, staying 'unknown'"
                )

        # Scaling unknown segments
        if obj["class"] == "unknown":
            # Normlizing (0, IMG_HEIGHT * IMG_WIDTH) -> (a,b)
            a = 1.01
            b = 1.05
            scale = a + ((b - a) * pixel_count) / (H * W)
            print(f"Scaling unknown segment by {scale}")
            new_mask = expand_mask(seg_mask, scale)

            # New mask
            scaled_np = blank.copy()
            scaled_np[new_mask] = image[new_mask]
            pil2 = Image.fromarray(scaled_np)

            # Adjust thresholds
            wt_t = knn_weight_threshold  # * scale
            rd_t = knn_raw_threshold  # / scale
            pt_t = prompt_threshold  # * scale

            pred2, knn_res2, ens_res2 = classifier.hybrid_classify(
                pil2, wt_t, rd_t, pt_t, prompt_threshold_fault
            )
            if pred2 != "unknown":
                print(f"Resolved at scale {scale:.2f}: {pred2}")
                obj.update({"class": pred2, "knn_res": knn_res2, "ens_res": ens_res2})
            else:
                print("Still unknown after scaling")

        # Zooming unknown segments
        if obj["class"] == "unknown":
            pil3 = bbox_segment(image, seg_mask)

            pred3, knn_res3, ens_res3 = classifier.hybrid_classify(
                pil3,
                knn_weight_threshold,
                knn_raw_threshold,
                prompt_threshold,
                prompt_threshold_fault,
            )
            if pred3 != "unknown":
                print("Resolved after zoom")
                obj.update({"class": pred3, "knn_res": knn_res3, "ens_res": ens_res3})
            else:
                print("Still unknown after zooming")

        if obj["class"] != "unknown":
            output.append(obj)
        else:
            print("Could not classify the segment, skipping segment")

    print(f"Initial segments: {len(output)}, Merging segments")
    merged_output = merge_segments_if_similar(output)
    return merged_output


def image_class_list(segments):
    class_pixel_map = defaultdict(int)

    for seg in segments:
        class_name = seg["class"]
        pixel_count = seg["pixels"]
        class_pixel_map[class_name] += pixel_count

    result = [
        {"class": name, "pixels": pixels}
        for name, pixels in class_pixel_map.items()
        if name not in non_food and name not in coins_names
    ]
    return result


router = APIRouter()


@router.post("/upload")
async def upload_image(data: Base64Image):
    image_data = base64.b64decode(data.image.split(",")[1])
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((512, 512))
    results = segment_and_classify(image)
    coin = [data for data in results if data["class"] in coins_names]
    class_list = image_class_list(results)
    if not len(coin):
        return {"error": "No coins detected"}, convert_image_to_base64(np.array(image))
    pixel_mm = get_pixel_size_in_mm(coin[0]["pixels"], coin[0]["class"])
    result = {}
    for data in class_list:
        matching_calories = None
        for key, value in calories.items():
            if str(data["class"]).lower() in key.lower():
                matching_calories = value
                break  # Stop searching after the first match
        result[str(data["class"])] = (
            calculate_amount_of_calories(
                pixel_mm, data["pixels"], float(matching_calories.removesuffix(" cal"))
            )
            if matching_calories
            else None
        )

    return {
        "result": result,
        "image": convert_image_to_base64(show_segments_on_image(image, results)),
    }
