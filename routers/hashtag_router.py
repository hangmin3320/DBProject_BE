from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database import models
from schemas import post_schemas

router = APIRouter(
    prefix="/tags",
    tags=["hashtags"]
)

@router.get("/{tag_name}/posts", response_model=List[post_schemas.PostResponse])
def get_posts_by_hashtag(tag_name: str, db: Session = Depends(get_db)):
    db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.name == tag_name).first()
    if not db_hashtag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found")
    
    return db_hashtag.posts
