import base64
import numpy as np
from app.constants.coins import coin_to_width
import cv2
import matplotlib.pyplot as plt

def get_pixel_size_in_mm(coin_area_in_pixels: int, coin_type: str):
    real_radius_mm = coin_to_width[coin_type] / 2  # Convert diameter to radius
    real_area_mm2 = np.pi * (real_radius_mm ** 2)  # Area of the coin in mm^2
    pixel_area_mm2 = real_area_mm2 / coin_area_in_pixels  # Area per
    return np.sqrt(pixel_area_mm2)  # Return the pixel size in mm

def calculate_amount_of_calories(pixel_size_in_mm, pixel_count, cal_per_100g):
    thickness_mm = 15  # in mm
    density_g_per_mm3 = 0.001  # in g/mm^3, assuming a density of 1 g/cm^3
    area_mm2 = pixel_count * pixel_size_in_mm
    volume_mm3 = area_mm2 * thickness_mm
    mass_g = volume_mm3 * density_g_per_mm3
    return np.round(((mass_g / 100) * cal_per_100g), 2)

def remove_duplicate_segments_from_masks(masks):
    print(f"Before deduplication: {len(masks)} masks")
    unique_masks = []
    for i, m1 in enumerate(masks):
        is_duplicate = False
        for m2 in unique_masks:
            inter = np.logical_and(m1["segmentation"], m2["segmentation"])
            overlap = np.sum(inter) / min(np.sum(m1["segmentation"]), np.sum(m2["segmentation"]))
            if overlap > 0.5:
                print(f"Mask {i} is over 50% overlapping with another, removing")
                is_duplicate = True
                break
        if not is_duplicate:
            unique_masks.append(m1)
    print(f"After deduplication: {len(unique_masks)} masks")
    return unique_masks

def merge_segments_if_similar(segments, image):
    i = 0
    while i < len(segments):
        base = segments[i]
        j = i + 1
        while j < len(segments):
            candidate = segments[j]
            if base['class'] == candidate['class']:
                merged_mask = np.logical_or(base["mask"], candidate["mask"])
                masked_image = image.copy()
                masked_image[~merged_mask] = 0
                print(f"Similar class, Merged {j} ({candidate['class']}) into {i} ({base['class']}) (removing idx {j})")

                base["mask"] = merged_mask
                base["pixels"] = np.sum(merged_mask)
                segments.pop(j)
            else:
                j += 1
        i += 1

    print(f"After merging: {len(segments)} segments kept")
    return segments

def show_segments_on_image(image, segments):
    overlay = np.array(image)
    color_map = plt.colormaps.get_cmap("tab20")

    for i, seg in enumerate(segments):
        mask = seg["mask"]
        class_name = seg["class"]

        # if class_name not in food_names:
        #     continue

        # Get a consistent color per segment
        color = (np.array(color_map(i / max(1, len(segments))))[:3] * 255).astype(np.uint8)

        colored_mask = np.zeros_like(image, dtype=np.uint8)
        for c in range(3):
            colored_mask[:, :, c] = mask.astype(np.uint8) * color[c]

        overlay = cv2.addWeighted(overlay, 1.0, colored_mask, 0.5, 0)

        ys, xs = np.where(mask)
        if len(xs) > 0 and len(ys) > 0:
            x, y = xs.min(), ys.min()
            label = f"{class_name}"
            cv2.putText(overlay, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 2, cv2.LINE_AA)
            
    return overlay

def convert_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_image}"



