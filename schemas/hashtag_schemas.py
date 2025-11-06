from pydantic import BaseModel

class HashtagBase(BaseModel):
    name: str

class HashtagCreate(HashtagBase):
    pass

class HashtagResponse(HashtagBase):
    hashtag_id: int

    class Config:
        from_attributes = True
