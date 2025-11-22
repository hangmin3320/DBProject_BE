from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database import models
from schemas import user_schemas
from auth import auth

router = APIRouter(
    tags=["follows"]
)

@router.post("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if user_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself")

    user_to_follow = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    follow_relation = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.user_id,
        models.Follow.following_id == user_id
    ).first()

    if follow_relation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already following this user")

    new_follow = models.Follow(follower_id=current_user.user_id, following_id=user_id)
    db.add(new_follow)

    # Update counts
    current_user.following_count += 1
    user_to_follow.follower_count += 1
    
    db.commit()

@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user_to_unfollow = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user_to_unfollow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    follow_relation = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.user_id,
        models.Follow.following_id == user_id
    ).first()

    if not follow_relation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not following this user")

    db.delete(follow_relation)

    # Update counts
    current_user.following_count -= 1
    user_to_unfollow.follower_count -= 1

    db.commit()

@router.get("/{user_id}/followers", response_model=List[user_schemas.UserResponse])
def get_followers(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    followers = db.query(models.User).join(models.Follow, models.User.user_id == models.Follow.follower_id).filter(models.Follow.following_id == user_id).all()
    return followers

@router.get("/{user_id}/following", response_model=List[user_schemas.UserResponse])
def get_following(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    following = db.query(models.User).join(models.Follow, models.User.user_id == models.Follow.following_id).filter(models.Follow.follower_id == user_id).all()
    return following
