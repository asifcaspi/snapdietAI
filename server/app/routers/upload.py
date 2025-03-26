import io
import base64
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from app.models.b64_image_model import Base64Image

router = APIRouter()

@router.post("/upload")
async def upload_image(data: Base64Image):
    try:
        image_data = base64.b64decode(data.image.split(",")[1])
        image = Image.open(io.BytesIO(image_data))
        image.show()

        return JSONResponse(content={
            "message": "Image processed successfully",
            "size": len(image_data),
            "format": image.format,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")