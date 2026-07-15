import os
from typing import Union

from sqlalchemy import create_engine, Engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from yaml import safe_load, YAMLError


class PrefixNotAuthorized(ValueError):
    """Levée quand un préfixe public ne correspond à aucune base autorisée.

    Distincte des autres `ValueError` de configuration pour que l'appelant
    puisse répondre par un refus générique (sans révéler si la base existe)."""


class Intranet:
    _db_name: Union[str, None]
    _connection: Union[Engine, None]

    # Cache des engines par nom de base pour éviter de recréer un pool
    # de connexions (et donc de fuir des connexions Postgres) à chaque requête.
    _engines: dict[str, Engine] = {}

    def __init__(self, prefix: Union[str, None]):
        # `prefix` est le préfixe public extrait de l'idStream. Il est résolu
        # vers une clé de base interne via une table d'autorisation explicite
        # (cf. `resolve_prefix`), plutôt que d'être utilisé tel quel comme nom
        # de base. Cela empêche qu'un préfixe deviné cible une autre base.
        if prefix is None:
            raise ValueError("Database name is required")
        self._prefix = prefix
        self._db_name = Intranet.resolve_prefix(prefix)
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

        databases: dict = Intranet.retrieve_databases()
        schema = databases.get(self._db_name)
        if schema is None:
            # `resolve_prefix` a déjà validé la présence de la base ; ceci ne
            # devrait pas arriver, mais on refuse proprement le cas échéant.
            raise ValueError("Database engine not found")

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

    @staticmethod
    def _retrieve_config() -> dict:
        """Charge et parse le fichier de configuration YAML complet."""
        config_file = os.getenv('CONFIG_FILE')
        if not config_file:
            raise ValueError("CONFIG_FILE environment variable not set")

        try:
            with open(config_file, "r") as file:
                try:
                    config: dict = safe_load(stream=file)
                except YAMLError as er:
                    raise ValueError(f"Invalid configuration file: {er}")
        except FileNotFoundError:
            raise ValueError("Configuration file not found")

        return config or {}

    @staticmethod
    def retrieve_databases() -> dict:
        """
        The function retrieves a list of database names from a configuration file.
        :return: A list of strings representing the names of databases.
        """
        databases = Intranet._retrieve_config().get('database')
        if not databases:
            raise ValueError("No 'database' section found in configuration file")

        return databases

    @staticmethod
    def available_prefixes() -> list[str]:
        """
        Liste des préfixes publics autorisés par la configuration.

        - Clés de la table `prefixes` si elle est présente (mode table
          d'autorisation explicite) ;
        - sinon, clés de `database` (mode identité, rétro-compatible).
        """
        config = Intranet._retrieve_config()
        prefixes = config.get('prefixes')
        if prefixes:
            return list(prefixes.keys())
        databases = config.get('database') or {}
        return list(databases.keys())

    @staticmethod
    def resolve_prefix(prefix: str) -> str:
        """
        Résout un préfixe public (extrait de l'idStream) vers la clé de base
        de données interne, via une table d'autorisation explicite.

        - Si la configuration contient une section `prefixes`, elle fait office
          de table d'autorisation : seuls les préfixes qui y figurent sont
          acceptés, et la valeur associée désigne la clé de `database` à
          utiliser. Le préfixe public (visible dans les URLs HLS) est ainsi
          découplé du nom interne de la base.
        - En l'absence de section `prefixes`, on retombe sur l'ancien
          comportement (mapping identité : le préfixe est lui-même la clé de
          base). Rétro-compatible avec les configs existantes.

        :raises PrefixNotAuthorized: si le préfixe n'est pas autorisé.
        """
        config = Intranet._retrieve_config()
        databases = config.get('database')
        if not databases:
            raise ValueError("No 'database' section found in configuration file")

        prefixes = config.get('prefixes')
        if prefixes:
            # Table d'autorisation explicite : le préfixe DOIT y figurer.
            db_key = prefixes.get(prefix)
            if db_key is None:
                raise PrefixNotAuthorized(f"Prefix not authorized: {prefix!r}")
        else:
            # Rétro-compat : convention de nommage (préfixe == clé de base).
            db_key = prefix

        if db_key not in databases:
            raise PrefixNotAuthorized(f"No database mapped for prefix: {prefix!r}")

        return db_key
