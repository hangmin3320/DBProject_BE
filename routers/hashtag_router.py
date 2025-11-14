from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from .post_router import _set_is_liked_for_posts
from database.database import get_db
from database import models
from schemas import post_schemas
from auth import auth

router = APIRouter(
    prefix="/tags",
    tags=["hashtags"]
)

@router.get("/{tag_name}/posts", response_model=List[post_schemas.PostResponse])
def get_posts_by_hashtag(tag_name: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user_optional)):
    db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.name == tag_name).first()
    if not db_hashtag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found")

    # Get posts with user information included
    posts_with_user = db.query(models.Post).options(joinedload(models.Post.user)).filter(
        models.Post.hashtags.any(models.Hashtag.hashtag_id == db_hashtag.hashtag_id)
    ).all()

    _set_is_liked_for_posts(db, current_user, posts_with_user)

    return posts_with_user
