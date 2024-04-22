from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import PostgresDsn
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_CONNECTION = os.environ.get("DEFAULT_ENGINE") or 'bardv'

# Function to create a new engine and add it to the engines dictionary
engines_dict = {}


def add_engine(engine_name: str,  db_name: str, db_user: str = 'POSTGRES_USER', db_pass: str = 'POSTGRES_PASSWORD',
               db_host: str = 'POSTGRES_HOST') -> None:
    DATABASE_USER = os.environ.get(db_user)
    DATABASE_PASSWORD = os.environ.get(db_pass)
    DATABASE_HOST = os.environ.get(db_host)

    engine = create_engine(PostgresDsn.build(
        scheme="postgresql",
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        path=f"/{db_name or ''}",
    ))
    engines_dict[engine_name] = engine


# Les base de donnees
add_engine('bardv', os.environ.get('POSTGRES_DB_BARD_DEV'))
add_engine('barpd', os.environ.get('POSTGRES_DB_BARD_PROD'))


def get_db(engine_name: str = DEFAULT_CONNECTION) -> Session:
    engine = engines_dict[engine_name]
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()

def dbs():
    return engines_dict


Base = declarative_base()
