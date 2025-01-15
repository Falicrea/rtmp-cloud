import os
from typing import Union

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from yaml import safe_load, YAMLError


class Intranet:
    _db_name: Union[str, None]
    _connection: Union[Engine, None]

    def __init__(self, db_name: Union[str, None]):
        if db_name is None:
            raise ValueError("Database name is required")
        self._db_name = db_name
        self._connection = None
        self._setup()

    def get_session(self) -> sessionmaker[Session]:
        """
        The function returns a database session based on the specified engine name.
        :return: A Session object is being returned.
        """
        return sessionmaker(bind=self._connection, autocommit=False, autoflush=False)

    def _setup(self):
        # This block of code is reading a YAML file named "defined.yaml" located in the "./configs" directory.
        # It then loads the content of the YAML file using the `safe_load` function from the `yaml` module.
        try:
            with open(os.getenv('CONFIG_FILE'), "r") as file:
                try:
                    config: dict = safe_load(stream=file)
                    databases = config.get('database')
                except YAMLError as er:
                    print(er.__str__())
                finally:
                    file.close()

            for db_key_name in databases.keys():
                if db_key_name != self._db_name:
                    continue

                schema: dict = databases.get(db_key_name)
                postgres_dsn_url = f"postgresql://{schema.get('username')}:{schema.get('password')}@{schema.get('host')}/{schema.get('name')}"
                self._connection = create_engine(postgres_dsn_url, pool_timeout=1800)
                break

            if self._connection is None:
                raise ValueError("Database engine not found")

        except FileNotFoundError:
            raise ValueError("Configuration file not found")
