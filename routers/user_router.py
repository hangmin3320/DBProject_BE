from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import or_

from .post_router import _set_is_liked_for_posts
from database.database import get_db
from database import models
from schemas import user_schemas, post_schemas
from auth import auth

router = APIRouter(
    tags=["users"]
)

@router.get("/search", response_model=List[user_schemas.UserResponse])
def search_users(q: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Search query cannot be empty")
    
    users = db.query(models.User).filter(
        models.User.username.ilike(f"%{q}%")
    ).offset(skip).limit(limit).all()
    return users

@router.post("/signup", response_model=user_schemas.UserResponse)
def create_user(user: user_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, password=hashed_password, bio=user.bio)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token")
def login_for_access_token(form_data: user_schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=user_schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=user_schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=user_schemas.UserResponse)
def update_user(user_id: int, user_update: user_schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}/password", response_model=user_schemas.UserResponse)
def update_password(user_id: int, password_update: user_schemas.PasswordUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to change this password")

    db_user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not auth.verify_password(password_update.old_password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    db_user.password = auth.get_password_hash(password_update.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}/posts", response_model=List[post_schemas.PostResponse])
def get_user_posts(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user_optional)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Get posts with user information included
    posts = db.query(models.Post).options(joinedload(models.Post.user)).filter(
        models.Post.user_id == user_id
    ).order_by(models.Post.created_at.desc()).all()

    _set_is_liked_for_posts(db, current_user, posts)

    return posts