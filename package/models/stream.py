from sqlalchemy import Column, Boolean, String, Integer, Date
from . import Base


class Stream(Base):
    __tablename__ = "Streaming"

    id = Column(Integer, primary_key=True)
    idStream = Column(String, unique=True, index=True)
    live = Column(Boolean)
    completedAt = Column(Date)
    m3u8Url = Column(String, default=None)
    mpdUrl = Column(String, default=None)
    flvsUrl = Column(String, default=None)
    createdAt = Column(Date)
    updatedAt = Column(Date)
