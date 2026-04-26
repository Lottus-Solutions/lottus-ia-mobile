from contextlib import contextmanager
from typing import Any, Iterator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from app.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self._pool = MySQLConnectionPool(
            pool_name="lottus_pool",
            pool_size=5,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
        )

    @contextmanager
    def cursor(self, dictionary: bool = True) -> Iterator[Any]:
        connection = self._pool.get_connection()
        cursor = connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
