from datetime import datetime

from sqlalchemy import insert, select, update

from queuectl.database.db import engine
from queuectl.database.schema import jobs


class JobRepository:
    def enqueue(self, command: str):
        now = datetime.utcnow()

        with engine.begin() as connection:
            result = connection.execute(
                insert(jobs).values(
                    command=command,
                    state="pending",
                    attempts=0,
                    max_retries=3,
                    claimed_by=None,
                    claimed_at=None,
                    next_retry_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )

        return result.inserted_primary_key[0]

    def claim_job(self, worker_id: str):
        now = datetime.utcnow()

        oldest_pending_job_id = (
            select(jobs.c.id)
            .where(jobs.c.state == "pending")
            .order_by(jobs.c.created_at.asc(), jobs.c.id.asc())
            .limit(1)
            .scalar_subquery()
        )

        with engine.begin() as connection:
            result = connection.execute(
                update(jobs)
                .where(
                    jobs.c.id == oldest_pending_job_id,
                    jobs.c.state == "pending",
)
                .values(
                    state="processing",
                    claimed_by=worker_id,
                    claimed_at=now,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def mark_completed(self, job_id: int):
        raise NotImplementedError

    def mark_failed(self, job_id: int):
        raise NotImplementedError

    def retry_job(self, job_id: int):
        raise NotImplementedError

    def move_to_dlq(self, job_id: int):
        raise NotImplementedError

    def get_pending_jobs(self):
        raise NotImplementedError

    def get_processing_jobs(self):
        raise NotImplementedError

    def get_dlq_jobs(self):
        raise NotImplementedError