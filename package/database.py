import os
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from yaml import safe_load, YAMLError

default_connection = ''

# Function to create a new engine and add it to the engines dictionary
CONNECTION_DATABASE = {}


def add_engine(id: str, db_name: Union[str, None], db_user: Union[str, None] = None, db_pass: str = '',
               db_host: str = '') -> bool:
    postgres_dsn_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(postgres_dsn_url, pool_timeout=1800)
    if engine is not None:
        CONNECTION_DATABASE[id] = engine
        return True

    return False


# This block of code is reading a YAML file named "defined.yaml" located in the "./configs" directory.
# It then loads the content of the YAML file using the `safe_load` function from the `yaml` module.
def load_engine():
    global default_connection
    with open(os.getenv('CONFIG_FILE'), "r") as stream:
        try:
            config: dict = safe_load(stream=stream)
            databases = config.get('database')
            for id in databases.keys():
                schema: dict = databases.get(id)
                add_engine(
                    id=id,  # Connection database reference
                    db_name=schema.get('name'),
                    db_user=schema.get('username'),
                    db_pass=schema.get('password'),
                    db_host=schema.get('host'))

                if schema.get('default', False) and schema['default'] == 1:
                    default_connection = id

                print(f"Database engine load: {id}")
        except YAMLError as er:
            print(er)
        stream.close()


def retrieve_connection(id: str) -> Session:
    """
    The function returns a database session based on the specified engine name.
    
    :param id: Represents the id of the database engine to be used for establishing a connection.
    It is used to retrieve the corresponding engine from the `CONNECTION_DATABASE` dictionary
    :type id: str
    :return: A Session object is being returned.
    """
    global default_connection
    engine = CONNECTION_DATABASE[id if id is not None else default_connection]
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()
