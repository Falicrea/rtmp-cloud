from sqlalchemy import Column, Boolean, String, Integer, Date
from . import model


class Stream(model.Base):
    __tablename__ = "Streaming"

    id = Column(Integer, primary_key=True)
    idStream = Column(String, unique=True, index=True)
    live = Column(Boolean)
    m3u8Url = Column(String, default=None)
    recorded = Column(Boolean, default=False)
    createdAt = Column(Date)
    updatedAt = Column(Date)
