from PIL import Image

width_on_client = 300
height_on_client = 300

# x_position_on_client, y_position_on_client = (30, 20)

coin_size = 40

COIN_WIDTH = 22 # in mm

def get_pixel_size_in_mm(image: Image.Image):
    heigh, width = image.size
    scaleWidth = width / width_on_client
    
    coin_pixel_width = coin_size * scaleWidth
    print(COIN_WIDTH / coin_pixel_width)
    return COIN_WIDTH / coin_pixel_width

def calculate_amount_of_calories(pixel_size_in_mm, pixel_count, cal_per_100g):
    thickness_mm = 15  # in mm
    density_g_per_mm3 = 0.001  # in g/mm^3, assuming a density of 1 g/cm^3
    area_mm2 = pixel_count * pixel_size_in_mm
    volume_mm3 = area_mm2 * thickness_mm
    mass_g = volume_mm3 * density_g_per_mm3
    return ((mass_g / 100) * cal_per_100g).quantize(0.01)  # Round to 2 decimal places

    




