from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database.database import get_db
from database import models
from schemas import post_schemas
from auth import auth

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

@router.post("/", response_model=post_schemas.PostResponse)
def create_post(post: post_schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = models.Post(**post.model_dump(), user_id=current_user.user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/", response_model=List[post_schemas.PostResponse])
def read_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, user_id: Optional[int] = None, sort_by: str = 'latest'):
    query = db.query(models.Post)

    if user_id:
        query = query.filter(models.Post.user_id == user_id)

    if sort_by == 'likes':
        query = query.order_by(models.Post.like_count.desc())
    else: # Default to 'latest'
        query = query.order_by(models.Post.created_at.desc())

    posts = query.offset(skip).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=post_schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/{post_id}", response_model=post_schemas.PostResponse)
def update_post(post_id: int, post_update: post_schemas.PostUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if db_post.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    for key, value in post_update.model_dump(exclude_unset=True).items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if db_post.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    
    db.delete(db_post)
    db.commit()
    return
