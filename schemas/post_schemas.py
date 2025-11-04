from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PostBase(BaseModel):
    content: str

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    post_id: int
    user_id: int
    created_at: datetime
    like_count: int

    class Config:
        from_attributes = True

class PostUpdate(PostBase):
    pass
