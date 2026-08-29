import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


load_dotenv()


@lru_cache
def get_engine():
    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise ValueError("POSTGRES_PASSWORD is not set.")

    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POSTGRES_USER"),
        password=password,
        host=os.getenv("DASHBOARD_POSTGRES_HOST"),
        port=int(os.getenv("DASHBOARD_POSTGRES_PORT")),
        database=os.getenv("POSTGRES_DB"),
    )

    return create_engine(url)