import os
from typing import Union

from sqlalchemy import create_engine, Engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from yaml import safe_load, YAMLError


class Intranet:
    _db_name: Union[str, None]
    _connection: Union[Engine, None]

    # Cache des engines par nom de base pour éviter de recréer un pool
    # de connexions (et donc de fuir des connexions Postgres) à chaque requête.
    _engines: dict[str, Engine] = {}

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
        return sessionmaker(bind=self._connection, autoflush=False)

    def _setup(self):
        # Réutilise l'engine déjà créé pour cette base si disponible.
        cached = Intranet._engines.get(self._db_name)
        if cached is not None:
            self._connection = cached
            return

        try:
            databases: dict = Intranet.retrieve_databases()
            for db_key_name in databases.keys():
                if db_key_name != self._db_name:
                    continue

                schema: dict = databases.get(db_key_name)
                host = str(schema.get('host') or '')
                port = None
                if ':' in host:
                    host, port_str = host.rsplit(':', 1)
                    port = int(port_str) if port_str.isdigit() else None
                postgres_dsn_url = URL.create(
                    "postgresql",
                    username=schema.get('username'),
                    password=schema.get('password'),
                    host=host,
                    port=port,
                    database=schema.get('name'),
                )
                self._connection = create_engine(
                    postgres_dsn_url,
                    pool_timeout=30,  # Wait up to 30 seconds for a connection
                    pool_pre_ping=True,
                )
                Intranet._engines[self._db_name] = self._connection
                break

            if self._connection is None:
                raise ValueError("Database engine not found")

        except FileNotFoundError:
            raise ValueError("Configuration file not found")

    @staticmethod
    def retrieve_databases() -> dict:
        """
        The function retrieves a list of database names from a configuration file.
        :return: A list of strings representing the names of databases.
        """
        config_file = os.getenv('CONFIG_FILE')
        if not config_file:
            raise ValueError("CONFIG_FILE environment variable not set")

        try:
            # Lit le fichier de configuration YAML et en extrait la section `database`.
            with open(config_file, "r") as file:
                try:
                    config: dict = safe_load(stream=file)
                except YAMLError as er:
                    raise ValueError(f"Invalid configuration file: {er}")

            databases = (config or {}).get('database')
            if not databases:
                raise ValueError("No 'database' section found in configuration file")

        except FileNotFoundError:
            raise ValueError("Configuration file not found")

        return databases