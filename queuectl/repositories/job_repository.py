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
        now = datetime.utcnow()

        with engine.begin() as connection:
            result = connection.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="completed",
                    claimed_by=None,
                    claimed_at=None,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def mark_failed(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as connection:
            result = connection.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    attempts=jobs.c.attempts + 1,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def retry_job(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as connection:
            current_job = connection.execute(
                select(jobs.c.attempts, jobs.c.max_retries).where(jobs.c.id == job_id)
            ).mappings().first()

            if current_job is None:
                return None

            if current_job["attempts"] < current_job["max_retries"]:
                result = connection.execute(
                    update(jobs)
                    .where(jobs.c.id == job_id)
                    .values(
                        state="pending",
                        claimed_by=None,
                        claimed_at=None,
                        next_retry_at=now,
                        updated_at=now,
                    )
                    .returning(jobs)
                )
            else:
                result = connection.execute(
                    update(jobs)
                    .where(jobs.c.id == job_id)
                    .values(
                        state="dlq",
                        updated_at=now,
                    )
                    .returning(jobs)
                )

            return result.mappings().first()

    def move_to_dlq(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as connection:
            result = connection.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="dlq",
                    claimed_by=None,
                    claimed_at=None,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def get_pending_jobs(self):
        with engine.connect() as connection:
            result = connection.execute(
                select(jobs).where(jobs.c.state == "pending").order_by(jobs.c.created_at.asc())
            )

            return result.mappings().all()

    def get_processing_jobs(self):
        with engine.connect() as connection:
            result = connection.execute(
                select(jobs).where(jobs.c.state == "processing")
            )

            return result.mappings().all()

    def get_dlq_jobs(self):
        with engine.connect() as connection:
            result = connection.execute(
                select(jobs).where(jobs.c.state == "dlq")
            )

            return result.mappings().all()