from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .hashtag_schemas import HashtagResponse
from .user_schemas import UserResponse

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
    user: UserResponse  # 사용자 정보 포함
    created_at: datetime
    like_count: int
    is_liked: Optional[bool] = None  # 피드에서 사용자 좋아요 상태 표시를 위한 필드
    hashtags: List[HashtagResponse] = []
    images: List[PostImageResponse] = []

    class Config:
        from_attributes = True
