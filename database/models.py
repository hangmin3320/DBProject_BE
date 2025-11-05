from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.database import Base

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="comment_owner")
    likes = relationship("Like", back_populates="like_owner")

    # Relationships for followers/following
    followers = relationship(
        "Follow",
        foreign_keys=[Follow.following_id],
        backref="following_user",
        cascade="all, delete-orphan"
    )
    following = relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        backref="follower_user",
        cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    like_count = Column(Integer, default=0)

    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post")
    likes = relationship("Like", back_populates="liked_post")

class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    comment_owner = relationship("User", back_populates="comments")
    parent_post = relationship("Post", back_populates="comments")

class Like(Base):
    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    like_owner = relationship("User", back_populates="likes")
    liked_post = relationship("Post", back_populates="likes")
