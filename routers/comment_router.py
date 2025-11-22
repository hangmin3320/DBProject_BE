from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database import models
from schemas import comment_schemas
from auth import auth

router = APIRouter(
    tags=["comments"]
)

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
