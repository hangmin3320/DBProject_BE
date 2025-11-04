from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database import models
from schemas import comment_schemas
from auth import auth

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

@router.post("/posts/{post_id}/comments", response_model=comment_schemas.CommentResponse)
def create_comment(post_id: int, comment: comment_schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_comment = models.Comment(**comment.model_dump(), post_id=post_id, user_id=current_user.user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/posts/{post_id}/comments", response_model=List[comment_schemas.CommentResponse])
def read_comments_for_post(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).offset(skip).limit(limit).all()
    return comments

@router.put("/{comment_id}", response_model=comment_schemas.CommentResponse)
def update_comment(comment_id: int, comment_update: comment_schemas.CommentUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if db_comment.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this comment")
    
    for key, value in comment_update.model_dump(exclude_unset=True).items():
        setattr(db_comment, key, value)
    
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if db_comment.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")
    
    db.delete(db_comment)
    db.commit()
    return
