from datetime import datetime

from sqlalchemy import insert, select, update, delete

from queuectl.database.db import engine
from queuectl.database.schema import workers


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

    def request_stop_all(self):
        with engine.begin() as conn:
            conn.execute(
                update(workers)
                .values(
                    stop_requested=True,
                )
            )

    def should_stop(self, worker_id: str):
        with engine.connect() as conn:
            row = conn.execute(
                select(workers.c.stop_requested)
                .where(workers.c.worker_id == worker_id)
            ).first()

            if row is None:
                return True

            return row[0]

    def unregister(self, worker_id: str):
        with engine.begin() as conn:
            conn.execute(
                delete(workers)
                .where(workers.c.worker_id == worker_id)
            )

    def get_workers(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(workers)
            )

            return result.mappings().all()

    def active_count(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(workers)
                .where(workers.c.status == "running")
            )

            return len(result.fetchall())