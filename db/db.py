import os
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


dotenv.load_dotenv()

Base = declarative_base()

from .models import Car


def create_db_engine(db_type="pgsql"):
    """
    Performs database engine connection using database settings from .env
    Returns sqlalchemy engine instance

    Args:
        db_type (str): 'sqlite' or 'pgsql'.

    Returns:
        sqlalchemy.engine.base.Engine:
    """

    dbname = os.getenv("POSTGRES_DB", "db_car")
    if db_type == "pgsql":
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    else:
        database_url = f"sqlite:///{dbname}_sql.db"

    return create_engine(database_url)

def create_tables(engine):
    Base.metadata.create_all(engine)

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
