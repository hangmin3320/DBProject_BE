from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .hashtag_schemas import HashtagResponse

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

    class Config:
        from_attributes = True
