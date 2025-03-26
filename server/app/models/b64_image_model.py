from pydantic import BaseModel

class Base64Image(BaseModel):
    image: str  # Base64-encoded image string