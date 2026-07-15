from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uuid = Column(String(36), nullable=False, unique=True)


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    collection_id = Column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    uuid = Column(String(36), nullable=False, unique=True)
    creation_time = Column(DateTime(timezone=True), nullable=False, default=func.now())
    modification_time = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    version_state = Column(String(32), nullable=False, default="uploading_items")
    name = Column(String(250), nullable=False)
    description = Column(String, nullable=True)

    collection = relationship("Collection")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    version_id = Column(
        Integer,
        ForeignKey("versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    uuid = Column(String(36), nullable=False)
    path = Column(String(1000), nullable=False)
    data_hash = Column(String(64), nullable=False)
    storage_link = Column(String(250), nullable=False)
    uploaded = Column(Boolean(), nullable=False, default=False)

    version = relationship("Version")

    __table_args__ = (
        UniqueConstraint("version_id", "uuid", name="unique_version_item_uuid"),
        UniqueConstraint("version_id", "path", name="unique_version_item_path"),
    )
