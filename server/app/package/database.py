from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import PostgresDsn
from dotenv import load_dotenv
from yaml import safe_load, YAMLError

load_dotenv()

CONFIG_FILE = "./configs/defined.yaml"
DEFAULT_CONNECTION = ''

# Function to create a new engine and add it to the engines dictionary
engines_dict = {}


def add_engine(engine_name: str, db_name: Union[str, None], db_user: str = '', db_pass: str = '',
               db_host: str = '') -> None:
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
    """
    engine = create_engine(PostgresDsn.build(
        scheme="postgresql",
        user=db_user,
        password=db_pass,
        host=db_host,
        path=f"/{db_name or ''}",
    ))
    engines_dict[engine_name] = engine



# This block of code is reading a YAML file named "defined.yaml" located in the "./configs" directory.
# It then loads the content of the YAML file using the `safe_load` function from the `yaml` module.
def load_engine():
    with open(CONFIG_FILE, "r") as stream:
        try:
            config = safe_load(stream=stream)
            databases = config.get('database')
            for database_name in databases.keys():
                schema: dict = databases.get(database_name)
                host = schema['dbhost']
                dbname = schema['dbname']
                username = schema['dbuser']
                password = schema['dbpass']

                add_engine(
                    engine_name=database_name,
                    db_name=dbname,
                    db_user=username,
                    db_pass=password,
                    db_host=host)

                if schema.get('default') and schema['default'] == 1:
                    DEFAULT_CONNECTION = database_name

                print(f"Database engine load: {database_name}")
        except YAMLError as er:
            print(er)


def get_db(engine_name: str = DEFAULT_CONNECTION) -> Session:
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
