from datetime import datetime, timedelta

from sqlalchemy import delete, insert, select, update, func, and_, or_

from queuectl.database.db import engine
from queuectl.database.schema import workers
from queuectl.repositories.config_repository import ConfigRepository


class WorkerRepository:

    def register(self, worker_id: str, pid: int):
        now = datetime.utcnow()

        with engine.begin() as conn:
            conn.execute(
                insert(workers).values(
                    worker_id=worker_id,
                    pid=pid,
                    status="running",
                    heartbeat=now,
                    started_at=now,
                    stop_requested=False,
                )
            )

    def heartbeat(self, worker_id: str):
        with engine.begin() as conn:
            conn.execute(
                update(workers)
                .where(workers.c.worker_id == worker_id)
                .values(
                    heartbeat=datetime.utcnow(),
                )
            )

    def should_stop(self, worker_id: str):
        with engine.connect() as conn:
            row = conn.execute(
                select(workers.c.stop_requested)
                .where(workers.c.worker_id == worker_id)
            ).first()

            return True if row is None else row[0]

    def request_stop(self, worker_id: str):
        with engine.begin() as conn:
            conn.execute(
                update(workers)
                .where(workers.c.worker_id == worker_id)
                .values(stop_requested=True)
            )

    def request_stop_all(self):
        with engine.begin() as conn:
            conn.execute(
                update(workers)
                .values(stop_requested=True)
            )

    def mark_stopped(self, worker_id: str):
        with engine.begin() as conn:
            conn.execute(
                update(workers)
                .where(workers.c.worker_id == worker_id)
                .values(
                    status="stopped",
                    heartbeat=datetime.utcnow(),
                    stop_requested=True,
                )
            )

    def unregister(self, worker_id: str):
        with engine.begin() as conn:
            conn.execute(
                delete(workers)
                .where(workers.c.worker_id == worker_id)
            )

    def get_worker(self, worker_id: str):
        with engine.connect() as conn:
            return conn.execute(
                select(workers)
                .where(workers.c.worker_id == worker_id)
            ).mappings().first()

    def get_workers(self):
        with engine.connect() as conn:
            return conn.execute(
                select(workers)
                .order_by(workers.c.started_at)
            ).mappings().all()

    def active_count(self):
        # Exclude workers whose heartbeat has gone stale (same threshold used by
        # job recovery). This handles both orphaned rows left by crashed/killed
        # processes that never ran unregister(), and workers pending a graceful stop.
        timeout = ConfigRepository().get_int("recovery-timeout")
        if timeout is None:
            timeout = 60
        threshold = datetime.utcnow() - timedelta(seconds=timeout)

        with engine.connect() as conn:
            return conn.execute(
                select(func.count())
                .select_from(workers)
                .where(
                    and_(
                        workers.c.status == "running",
                        workers.c.heartbeat >= threshold,
                    )
                )
            ).scalar_one()

    def stale_workers(self, timeout_seconds: int = 60):
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)

        with engine.connect() as conn:
            return conn.execute(
                select(workers)
                .where(
                    workers.c.heartbeat < threshold
                )
            ).mappings().all()

    def cleanup_stale(self, timeout_seconds: int = 60):
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)

        with engine.begin() as conn:
            conn.execute(
                delete(workers)
                .where(
                    workers.c.heartbeat < threshold
                )
            )