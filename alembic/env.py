from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Determine environment - default to development
FLASK_ENV = os.getenv("FLASK_ENV", "development")
print(f"Alembic running in {FLASK_ENV} mode")

# Set the database URL based on environment
if FLASK_ENV == "production":
    database_url = os.getenv('AZURE_SQL_CONNECTION_STRING')
    if database_url is None:
        raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set for production")
else:
    # Development - use TEST_DATABASE_URL or fallback to SQLite
    database_url = os.getenv('TEST_DATABASE_URL')
    if not database_url:
        # Fallback to SQLite in instance folder
        from pathlib import Path
        basedir = Path(__file__).parent.parent
        instance_path = basedir / "instance"
        instance_path.mkdir(exist_ok=True)
        database_url = f"sqlite:///{instance_path}/jarvus_app.db"
        print(f"Using development SQLite database: {database_url}")

config.set_main_option('sqlalchemy.url', str(database_url))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here
from jarvus_app.models.user import User
from jarvus_app.models.user_tool import UserTool
from jarvus_app.models.oauth import OAuthCredentials
from jarvus_app.models.tool_permission import ToolPermission
from jarvus_app.models.history import History
from jarvus_app.db import db

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
