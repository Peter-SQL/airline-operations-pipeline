import argparse
import os

import psycopg
from dotenv import load_dotenv

from config.paths import PROJECT_ROOT


load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airline_reliability")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

BUILD_GOLD_SQL = PROJECT_ROOT / "sql" / "ddl" / "build_gold.sql"


def get_connection():
    if not POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD is not set.")

    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def build_gold(year: int, month: int):
    if not BUILD_GOLD_SQL.exists():
        raise FileNotFoundError(
            f"Gold SQL file not found: {BUILD_GOLD_SQL}"
        )

    sql = BUILD_GOLD_SQL.read_text(encoding="utf-8")

    sql = sql.replace("%(year)s", str(year))
    sql = sql.replace("%(month)s", str(month))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print(f"Gold tables successfully rebuilt for {year}-{month:02d}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)

    args = parser.parse_args()

    build_gold(args.year, args.month)


if __name__ == "__main__":
    main()
