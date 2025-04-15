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

    




