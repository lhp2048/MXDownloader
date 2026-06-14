from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


DEFAULT_PLAYLIST_NAME = "全部下载"


class PlaylistORM(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    items: Mapped[list["PlaylistItemORM"]] = relationship(
        "PlaylistItemORM",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItemORM.sort_order",
    )


class PlaylistItemORM(Base):
    __tablename__ = "playlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    rel_path: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(512), default="")
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    playlist: Mapped["PlaylistORM"] = relationship("PlaylistORM", back_populates="items")


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)


class PlaylistItemCreate(BaseModel):
    rel_path: Optional[str] = None
    task_id: Optional[int] = None


class PlaylistItemResponse(BaseModel):
    id: int
    playlist_id: int
    rel_path: str
    title: str = ""
    name: str = ""
    size: int = 0
    media_type: str = ""
    task_id: Optional[int] = None
    sort_order: int = 0
    public_url: str = ""
    exists: bool = True
    added_at: Optional[datetime] = None


class PlaylistResponse(BaseModel):
    id: int
    name: str
    is_default: bool = False
    item_count: int = 0
    created_at: Optional[datetime] = None
