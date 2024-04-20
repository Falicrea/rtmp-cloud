from sqlalchemy import create_engine, Column, Boolean, String, Integer, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import PostgresDsn
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_CONNECTION = os.environ.get("DEFAULT_ENGINE") or 'bardv'

# Function to create a new engine and add it to the engines dictionary
engines_dict = {}


def add_engine(engine_name: str, db_user: str, db_pass: str, db_host: str, db_name: str):
    DATABASE_NAME = os.environ.get(db_name)
    DATABASE_USER = os.environ.get(db_user)
    DATABASE_PASSWORD = os.environ.get(db_pass)
    DATABASE_HOST = os.environ.get(db_host)

    engine = create_engine(PostgresDsn.build(
        scheme="postgresql",
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        path=f"/{DATABASE_NAME or ''}",
    ))
    engines_dict[engine_name] = engine

# Environnement de dev
add_engine('bardv',
           'POSTGRES_USER',
           'POSTGRES_PASSWORD',
           'POSTGRES_HOST',
           'POSTGRES_DB_BARD_DEV'
           )


def get_db(engine_name: str = DEFAULT_CONNECTION) -> Session:
    engine = engines_dict[engine_name]
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()

def dbs():
    return engines_dict


Base = declarative_base()


class Streaming(Base):
    __tablename__ = "Streaming"

    id = Column(Integer, primary_key=True)
    idStream = Column(String, unique=True, index=True)
    live = Column(Boolean)
    flvsUrl = Column(String, default=None)
    m3u8Url = Column(String, default=None)
    recorded = Column(Boolean, default=False)
    name = Column(String)
    description = Column(String)
    deleted = Column(Integer, default=0)
    deletedAt = Column(Date)
    createdAt = Column(Date)
    updatedAt = Column(Date)
