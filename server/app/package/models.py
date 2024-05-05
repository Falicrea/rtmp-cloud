from sqlalchemy import Column, Boolean, String, Integer, Date
from .database import Base


class Streaming(Base):
    __tablename__ = "Streaming"

    id = Column(Integer, primary_key=True)
    idStream = Column(String, unique=True, index=True)
    live = Column(Boolean)
    flvsUrl = Column(String, default=None)
    m3u8Url = Column(String, default=None)
    recorded = Column(Boolean, default=False)
    deleted = Column(Integer, default=0)
    deletedAt = Column(Date)
    createdAt = Column(Date)
    updatedAt = Column(Date)