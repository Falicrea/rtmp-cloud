import os
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import PostgresDsn
from yaml import safe_load, YAMLError

default_connection = ''

# Function to create a new engine and add it to the engines dictionary
engines_dict = {}

def add_engine(engine_name: str, db_name: Union[str, None], db_user: str = '', db_pass: str = '',
               db_host: str = '', schema: str = 'postgresql') -> bool:


    """
    The function `add_engine` creates a database engine for a specified engine name with optional
    database connection details.

    :param engine_name: The `engine_name` parameter is a string that represents the name of the engine
    being added to the `engines_dict`
    :type engine_name: str
    :param db_name: The `db_name` parameter is a string that represents the name of the database to
    connect to. It can also be `None` if no specific database name is provided
    :type db_name: Union[str, None]
    :param db_user: The `db_user` parameter in the `add_engine` function is used to specify the username
    for connecting to the database. It is a required parameter and must be provided when calling the
    function
    :type db_user: str
    :param db_pass: The `db_pass` parameter in the `add_engine` function is used to specify the password
    for the database connection. It is a required parameter and should be provided with the password
    needed to connect to the database
    :type db_pass: str
    :param db_host: The `db_host` parameter in the `add_engine` function represents the host address of
    the database server where the PostgreSQL database is running. It is a string parameter that
    specifies the hostname or IP address of the server
    :type db_host: str
    :type schema: str
    """
    if schema == 'postgresql':
        engine = create_engine(PostgresDsn.build(scheme="postgresql", user=db_user, password=db_pass, host=db_host, path=f"/{db_name or ''}",), pool_timeout=1800)
    else:
        engine = create_engine(f"{schema}+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}", echo='debug')

    if engine is not None:
        engines_dict[engine_name] = engine
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
            for connection in databases.keys():
                schema: dict = databases.get(connection)
                host = schema.get('dbhost')
                dbname = schema.get('dbname')
                username = schema.get('dbuser')
                password = schema.get('dbpass')

                add_engine(
                    engine_name=connection, # Connection database reference
                    db_name=dbname,
                    db_user=username,
                    db_pass=password,
                    db_host=host)

                if schema.get('default', False) and schema['default'] == 1:
                    default_connection = connection

                print(f"Database engine load: {connection}")
        except YAMLError as er:
            print(er)


def get_db(engine_name: str = default_connection) -> Session:
    """
    The function `get_db` returns a database session based on the specified engine name.
    
    :param engine_name: The `engine_name` parameter is a string that represents the name of the database
    engine to be used for establishing a connection. It is used to retrieve the corresponding engine
    from the `engines_dict` dictionary
    :type engine_name: str
    :return: A Session object is being returned.
    """
    engine = engines_dict[engine_name]
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()

def dbs():
    return engines_dict


Base = declarative_base()
