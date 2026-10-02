"""PostgreSQL connections via psycopg (no ORM, no query builder).

Rows come back as dicts (`dict_row`), so repositories read columns by name.
"""

from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


def connect(autocommit: bool = True) -> psycopg.Connection:
    """Open a new connection. The API only reads, so autocommit avoids
    leaving idle transactions open."""
    s = get_settings()
    return psycopg.connect(
        host=s.db_host,
        port=s.db_port,
        dbname=s.db_name,
        user=s.db_user,
        password=s.db_password,
        row_factory=dict_row,
        autocommit=autocommit,
        connect_timeout=5,
    )


def get_conn() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: one connection per request, always closed."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
