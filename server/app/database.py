from sqlalchemy import create_engine, Column, Boolean, String, Integer, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import PostgresDsn

SQLALCHEMY_DATABASE_URL = PostgresDsn.build(
    scheme="postgresql",
    user="",
    password="",
    host="",
    path=f"/{'' or ''}",
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Streaming(Base):
    __tablename__ = "Streaming"

    id = Column(Integer, primary_key=True)
    idStream = Column(String, unique=True, index=True)
    live = Column(Boolean)
    name = Column(String)
    description = Column(String)
    deleted = Column(Integer, default=0)
    deletedAt = Column(Date)
    createdAt = Column(Date)
    updatedAt = Column(Date)
