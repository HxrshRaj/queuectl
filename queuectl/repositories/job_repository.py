from datetime import datetime, timedelta

from sqlalchemy import and_, insert, or_, select, update

from queuectl.database.db import engine
from queuectl.database.schema import jobs


class JobRepository:
    def enqueue(self, command: str, max_retries: int = 3):
        now = datetime.utcnow()

        with engine.begin() as conn:
            result = conn.execute(
                insert(jobs).values(
                    command=command,
                    state="pending",
                    attempts=0,
                    max_retries=max_retries,
                    next_retry_at=None,
                    claimed_by=None,
                    claimed_at=None,
                    last_error=None,
                    created_at=now,
                    updated_at=now,
                    finished_at=None,
                )
            )

            return result.inserted_primary_key[0]

    def claim_job(self, worker_id: str):
        now = datetime.utcnow()

        with engine.begin() as conn:

            job = conn.execute(
                select(jobs)
                .where(
                    and_(
                        jobs.c.state == "pending",
                        or_(
                            jobs.c.next_retry_at.is_(None),
                            jobs.c.next_retry_at <= now,
                        ),
                    )
                )
                .order_by(jobs.c.created_at)
                .limit(1)
            ).mappings().first()

            if job is None:
                return None

            updated = conn.execute(
                update(jobs)
                .where(
                    and_(
                        jobs.c.id == job["id"],
                        jobs.c.state == "pending",
                    )
                )
                .values(
                    state="processing",
                    claimed_by=worker_id,
                    claimed_at=now,
                    updated_at=now,
                )
                .returning(jobs)
            ).mappings().first()

            return updated

    def mark_completed(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as conn:

            result = conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="completed",
                    claimed_by=None,
                    claimed_at=None,
                    finished_at=now,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def mark_failed(self, job_id: int, error: str):
        now = datetime.utcnow()

        with engine.begin() as conn:

            result = conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="failed",
                    attempts=jobs.c.attempts + 1,
                    last_error=error,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def retry_job(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as conn:

            job = conn.execute(
                select(jobs).where(jobs.c.id == job_id)
            ).mappings().first()

            if job is None:
                return None

            attempts = job["attempts"]
            max_retries = job["max_retries"]

            if attempts >= max_retries:
                return self.move_to_dead(job_id)

            delay = 2 ** attempts

            result = conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="pending",
                    claimed_by=None,
                    claimed_at=None,
                    next_retry_at=now + timedelta(seconds=delay),
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()
    def move_to_dead(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as conn:

            result = conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="dead",
                    claimed_by=None,
                    claimed_at=None,
                    finished_at=now,
                    updated_at=now,
                )
                .returning(jobs)
            )

            return result.mappings().first()

    def recover_processing_jobs(self, timeout_seconds: int = 60):
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)

        with engine.begin() as conn:

            result = conn.execute(
                update(jobs)
                .where(
                    and_(
                        jobs.c.state == "processing",
                        jobs.c.claimed_at < threshold,
                    )
                )
                .values(
                    state="pending",
                    claimed_by=None,
                    claimed_at=None,
                    updated_at=datetime.utcnow(),
                )
                .returning(jobs)
            )

            return result.mappings().all()

    def get_job(self, job_id: int):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs).where(jobs.c.id == job_id)
            )

            return result.mappings().first()

    def get_all_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs).order_by(jobs.c.created_at)
            )

            return result.mappings().all()

    def get_pending_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs)
                .where(jobs.c.state == "pending")
                .order_by(jobs.c.created_at)
            )

            return result.mappings().all()

    def get_processing_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs)
                .where(jobs.c.state == "processing")
                .order_by(jobs.c.created_at)
            )

            return result.mappings().all()

    def get_completed_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs)
                .where(jobs.c.state == "completed")
                .order_by(jobs.c.created_at)
            )

            return result.mappings().all()

    def get_failed_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs)
                .where(jobs.c.state == "failed")
                .order_by(jobs.c.created_at)
            )

            return result.mappings().all()

    def get_dead_jobs(self):
        with engine.connect() as conn:
            result = conn.execute(
                select(jobs)
                .where(jobs.c.state == "dead")
                .order_by(jobs.c.created_at)
            )

            return result.mappings().all()    