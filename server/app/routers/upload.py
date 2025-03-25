import io
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

router = APIRouter()

@router.post("/upload/")
async def upload_image(file: UploadFile = File()):
    # Simulate processing the image
    content = await file.read()
    image = Image.open(io.BytesIO(content))
    image.show()
    return JSONResponse(content={
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
    })