import os
import platform
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
from app.constants.device import device

output_file = os.path.join(
    os.path.join(os.path.dirname(__file__), "../../sam_vit_l_0b3195.pth")
)
if not os.path.exists(output_file):
    url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth"

    if platform.system() == "Windows":
        os.system(f'curl -o "{output_file}" {url}')
    else:
        os.system(f'wget -O "{output_file}" {url}')


sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to(device)
mask_generator = SamAutomaticMaskGenerator(sam, points_per_side=16)
