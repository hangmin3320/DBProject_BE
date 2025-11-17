from pydantic import BaseModel
from datetime import datetime
from .user_schemas import UserResponse

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    comment_id: int
    post_id: int
    user_id: int
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True

class CommentUpdate(CommentBase):
    pass
