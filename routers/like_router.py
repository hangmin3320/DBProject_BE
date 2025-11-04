from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database import models
from schemas import like_schemas
from auth import auth

router = APIRouter(
    prefix="/posts",
    tags=["likes"]
)

@router.post("/{post_id}/like", response_model=like_schemas.LikeResponse)
def toggle_like(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_like = db.query(models.Like).filter(
        models.Like.user_id == current_user.user_id,
        models.Like.post_id == post_id
    ).first()

    if db_like:
        # Unlike the post
        db.delete(db_like)
        db_post.like_count -= 1
        db.commit()
        db.refresh(db_post)
        raise HTTPException(status_code=200, detail="Post unliked")
    else:
        # Like the post
        new_like = models.Like(user_id=current_user.user_id, post_id=post_id)
        db.add(new_like)
        db_post.like_count += 1
        db.commit()
        db.refresh(db_post)
        db.refresh(new_like)
        return new_like

@router.get("/{post_id}/likes", response_model=List[like_schemas.LikeResponse])
def get_likes_for_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    likes = db.query(models.Like).filter(models.Like.post_id == post_id).all()
    return likes

@router.get("/users/{user_id}/likes", response_model=List[like_schemas.LikeResponse])
def get_liked_posts_by_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    likes = db.query(models.Like).filter(models.Like.user_id == user_id).all()
    return likes
