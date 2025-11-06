from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .hashtag_schemas import HashtagResponse

class PostImageResponse(BaseModel):
    image_id: int
    image_url: str

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content: str

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None

class PostResponse(PostBase):
    post_id: int
    user_id: int
    created_at: datetime
    like_count: int
    hashtags: List[HashtagResponse] = []
    images: List[PostImageResponse] = []

    class Config:
        from_attributes = True
