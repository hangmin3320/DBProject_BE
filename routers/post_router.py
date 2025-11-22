from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import re
import uuid
import shutil
from datetime import datetime, timedelta

from database.database import get_db
from database import models
from schemas import post_schemas, comment_schemas
from auth import auth

def _set_is_liked_for_posts(db: Session, current_user: Optional[models.User], posts: List[models.Post]):
    if not posts:
        return

    if not current_user:
        for post in posts:
            post.is_liked = False
        return

    liked_post_ids = {like.post_id for like in db.query(models.Like.post_id).filter(
        models.Like.user_id == current_user.user_id
    ).all()}

    for post in posts:
        post.is_liked = post.post_id in liked_post_ids

def get_or_create_hashtags(db: Session, content: str) -> List[models.Hashtag]:
    hashtag_names = set(re.findall(r"#(\w+)", content))
    hashtags = []
    for name in hashtag_names:
        db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.name == name).first()
        if not db_hashtag:
            db_hashtag = models.Hashtag(name=name)
            db.add(db_hashtag)
        hashtags.append(db_hashtag)
    return hashtags

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

@router.get("/feed", response_model=List[post_schemas.PostResponse])
def get_user_feed(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    following_ids = [f.following_id for f in current_user.following]

    if not following_ids:
        return []

    # Get the current user's liked post IDs to determine is_liked status
    liked_post_ids = [like.post_id for like in db.query(models.Like).filter(
        models.Like.user_id == current_user.user_id
    ).all()]

    feed_posts = db.query(models.Post).options(joinedload(models.Post.user)).filter(
        models.Post.user_id.in_(following_ids)
    ).order_by(models.Post.created_at.desc()).all()

    # Add is_liked information to each post
    for post in feed_posts:
        post.is_liked = post.post_id in liked_post_ids

    return feed_posts

@router.get("/trending", response_model=List[post_schemas.PostResponse])
def get_trending_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    trending_posts = db.query(models.Post).options(joinedload(models.Post.user)).filter(
        models.Post.created_at >= seven_days_ago
    ).order_by(models.Post.like_count.desc()).offset(skip).limit(limit).all()

    # For trending posts, is_liked will be set to None or False since there's no authenticated user context
    for post in trending_posts:
        post.is_liked = False

    return trending_posts


@router.post("", response_model=post_schemas.PostResponse)
def create_post(content: str = Form(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user), files: List[UploadFile] = File([])):
    try:
        # 1. Create Post and Hashtags
        hashtags = get_or_create_hashtags(db, content)
        db_post = models.Post(content=content, user_id=current_user.user_id, hashtags=hashtags)
        db.add(db_post)
        db.flush() # Flush to get post_id for images

        # 2. Handle Image Uploads
        allowed_mime_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        image_urls = []
        for file in files:
            # Validate file type
            if file.content_type not in allowed_mime_types:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type {file.content_type} not allowed. Only images are accepted.")

            file_extension = file.filename.split(".")[-1]
            file_name = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"uploads/images/{file_name}"
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            image_url = f"/uploads/images/{file_name}"
            db_image = models.PostImage(post_id=db_post.post_id, image_url=image_url)
            db.add(db_image)
            image_urls.append(image_url)

        db.commit()
        # Refresh the post with user information using joinedload
        db_post = db.query(models.Post).options(joinedload(models.Post.user)).filter(
            models.Post.post_id == db_post.post_id
        ).first()

        # Set is_liked to False for the newly created post (by the current user)
        db_post.is_liked = False

        return db_post

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[post_schemas.PostResponse])
def read_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, user_id: Optional[int] = None, sort_by: str = 'latest', current_user: models.User = Depends(auth.get_current_user_optional)):
    query = db.query(models.Post).options(joinedload(models.Post.user))

    if user_id:
        query = query.filter(models.Post.user_id == user_id)

    if sort_by == 'likes':
        query = query.order_by(models.Post.like_count.desc())
    else: # Default to 'latest'
        query = query.order_by(models.Post.created_at.desc())

    posts = query.offset(skip).limit(limit).all()
    _set_is_liked_for_posts(db, current_user, posts)
    return posts

@router.get("/{post_id}", response_model=post_schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user_optional)):
    post = db.query(models.Post).options(joinedload(models.Post.user)).filter(
        models.Post.post_id == post_id
    ).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Set is_liked status based on whether current user has liked the post
    if current_user:
        like_exists = db.query(models.Like).filter(
            models.Like.user_id == current_user.user_id,
            models.Like.post_id == post_id
        ).first()
        post.is_liked = like_exists is not None
    else:
        post.is_liked = False

    return post

@router.put("/{post_id}", response_model=post_schemas.PostResponse)
def update_post(post_id: int, post_update: post_schemas.PostUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if db_post.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    try:
        if post_update.content is not None:
            db_post.content = post_update.content
            db_post.hashtags = get_or_create_hashtags(db, post_update.content)
        
        db.commit()
        # Refresh the post with user information using joinedload
        db_post = db.query(models.Post).options(joinedload(models.Post.user)).filter(
            models.Post.post_id == post_id
        ).first()

        # Set is_liked to False when returning the updated post
        db_post.is_liked = False

        return db_post
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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

@router.post("/{post_id}/comments", response_model=comment_schemas.CommentResponse, tags=["comments"])
def create_comment(post_id: int, comment: comment_schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_comment = models.Comment(**comment.model_dump(), post_id=post_id, user_id=current_user.user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/{post_id}/comments", response_model=List[comment_schemas.CommentResponse], tags=["comments"])
def read_comments_for_post(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.post_id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = db.query(models.Comment).options(joinedload(models.Comment.user)).filter(models.Comment.post_id == post_id).offset(skip).limit(limit).all()
    return comments