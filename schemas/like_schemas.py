from pydantic import BaseModel
from datetime import datetime

class LikeResponse(BaseModel):
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True
