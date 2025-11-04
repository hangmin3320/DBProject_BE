from pydantic import BaseModel
from datetime import datetime

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    comment_id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CommentUpdate(CommentBase):
    pass
