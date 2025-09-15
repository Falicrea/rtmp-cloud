import os

from dotenv import load_dotenv
from yaml import safe_load

load_dotenv('../.env')

def test_configs():
    # Config file exist
    config_path = os.getenv('CONFIG_FILE')
    work_dir_path = os.getenv('WORK_DIR')

    assert config_path is not None
    assert work_dir_path is not None
    assert os.path.isfile(config_path)
    assert os.path.isdir(work_dir_path)

def test_database():
    with open(os.getenv('CONFIG_FILE'), "r") as file:
        content = file.read()

        assert 'database:' in content

        config:dict = safe_load(stream=content)
        databases = config.get('database')
        assert isinstance(databases, dict)

        for key_name in databases.keys():
            schema:dict = databases.get(key_name)

            assert 'username' in schema
            assert 'password' in schema
            assert 'host' in schema
            assert 'name' in schema

            #  test postgress database connection
            postgres_dsn_url = f"postgresql://{schema.get('username')}:{schema.get('password')}@{schema.get('host')}/{schema.get('name')}"
            import psycopg2
            conn = psycopg2.connect(postgres_dsn_url)
            assert conn is not None
            conn.close()

        file.close()