"""One session owns a database-wide lock; lost ownership is terminal."""

from sqlalchemy import text
from sqlalchemy.engine import URL, Connection
from sqlalchemy.exc import SQLAlchemyError

from crow_algo.database import PersistenceError, database_engine

LOCK_KEY = 0x43524F575F414C47


class OwnershipUnavailable(PersistenceError):
    pass


class OwnershipLost(PersistenceError):
    pass


class OwnerLock:
    """Dedicated, unpooled connection; never reconnect or reacquire implicitly.

    Future runners must call check before protected work and stop on failure.
    This is not an exchange-side fence against an already in-flight request.
    """

    def __init__(self, url: str | URL | None = None) -> None:
        self._engine = database_engine(url, dedicated=True)
        self._connection: Connection | None = None
        self._lost = False

    def __enter__(self) -> "OwnerLock":
        if self._connection is not None or self._lost:
            raise OwnershipUnavailable("ownership handle cannot be reused")
        try:
            connection = self._engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            )
            self._connection = connection
            acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY}
            ).scalar_one()
            if not acquired:
                raise OwnershipUnavailable("another session owns the trading lock")
        except SQLAlchemyError:
            self.close()
            raise OwnershipUnavailable("unable to acquire trading ownership") from None
        except OwnershipUnavailable:
            self.close()
            raise
        return self

    def check(self) -> None:
        connection = self._connection
        if self._lost or connection is None:
            raise OwnershipLost("trading ownership is not active")
        try:
            if connection.closed or connection.invalidated:
                raise OwnershipLost("trading ownership connection was lost")
            held = connection.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_locks "
                    "WHERE locktype='advisory' AND pid=pg_backend_pid() "
                    "AND classid=:high AND objid=:low AND objsubid=1 AND granted)"
                ),
                {"high": LOCK_KEY >> 32, "low": LOCK_KEY & 0xFFFFFFFF},
            ).scalar_one()
            if not held:
                raise OwnershipLost("trading ownership was released")
        except (SQLAlchemyError, OwnershipLost):
            self._lost = True
            self.close()
            raise OwnershipLost(
                "trading ownership was lost; stop protected work"
            ) from None

    def close(self) -> None:
        self._lost = True
        connection, self._connection = self._connection, None
        try:
            if connection is not None:
                connection.close()
        except SQLAlchemyError:
            pass  # A terminated session already released its advisory locks.
        finally:
            self._engine.dispose()

    def __exit__(self, *args: object) -> None:
        self.close()
