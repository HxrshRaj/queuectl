from datetime import datetime, timedelta

from sqlalchemy import and_, insert, or_, select, update, func

from queuectl.database.db import engine
from queuectl.database.schema import jobs, workers
from queuectl.repositories.config_repository import ConfigRepository


class JobRepository:

    def __init__(self):
        self.config = ConfigRepository()

    def enqueue(self, command: str):
        now = datetime.utcnow()

        max_retries = self.config.get_int("max-retries")
        if max_retries is None:
            max_retries = 3

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
        while True:
            now = datetime.utcnow()

            with engine.begin() as conn:

                job = conn.execute(
                    select(jobs.c.id)
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
                ).first()

                if job is None:
                    return None

                updated = conn.execute(
                    update(jobs)
                    .where(
                        and_(
                            jobs.c.id == job[0],
                            jobs.c.state == "pending",
                            or_(
                                jobs.c.next_retry_at.is_(None),
                                jobs.c.next_retry_at <= now,
                            ),
                        )
                    )
                    .values(
                        state="processing",
                        claimed_by=worker_id,
                        claimed_at=now,
                        updated_at=now,
                    )
                )

                if updated.rowcount == 1:
                    return conn.execute(
                        select(jobs)
                        .where(jobs.c.id == job[0])
                    ).mappings().first()

    def mark_completed(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as conn:
            conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="completed",
                    claimed_by=None,
                    claimed_at=None,
                    finished_at=now,
                    updated_at=now,
                )
            )

        return self.get_job(job_id)

    def mark_failed(self, job_id: int, error: str):
        now = datetime.utcnow()
        base = self.config.get_int("backoff-base")
        if base is None:
            base = 2

        with engine.begin() as conn:
            job = conn.execute(
                select(jobs).where(jobs.c.id == job_id)
            ).mappings().first()

            if job is None:
                return None

            attempts = job["attempts"] + 1

            if attempts >= job["max_retries"]:
                conn.execute(
                    update(jobs)
                    .where(jobs.c.id == job_id)
                    .values(
                        state="dead",
                        attempts=attempts,
                        last_error=error,
                        claimed_by=None,
                        claimed_at=None,
                        finished_at=now,
                        updated_at=now,
                    )
                )
            else:
                delay = base ** (attempts - 1)
                conn.execute(
                    update(jobs)
                    .where(jobs.c.id == job_id)
                    .values(
                        state="pending",
                        attempts=attempts,
                        last_error=error,
                        claimed_by=None,
                        claimed_at=None,
                        next_retry_at=now + timedelta(seconds=delay),
                        updated_at=now,
                    )
                )

        return self.get_job(job_id)

    def retry_job(self, job_id: int):

        job = self.get_job(job_id)

        if job is None:
            return None

        attempts = job["attempts"]

        if attempts >= job["max_retries"]:
            return self.move_to_dead(job_id)

        base = self.config.get_int("backoff-base")
        if base is None:
            base = 2

        delay = base ** attempts

        now = datetime.utcnow()

        with engine.begin() as conn:
            conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="pending",
                    claimed_by=None,
                    claimed_at=None,
                    next_retry_at=now + timedelta(seconds=delay),
                    updated_at=now,
                )
            )

        return self.get_job(job_id)

    def move_to_dead(self, job_id: int):
        now = datetime.utcnow()

        with engine.begin() as conn:
            conn.execute(
                update(jobs)
                .where(jobs.c.id == job_id)
                .values(
                    state="dead",
                    claimed_by=None,
                    claimed_at=None,
                    finished_at=now,
                    updated_at=now,
                )
            )

        return self.get_job(job_id)

    def retry_dead_job(self, job_id: int):

        now = datetime.utcnow()

        with engine.begin() as conn:
            conn.execute(
                update(jobs)
                .where(
                    and_(
                        jobs.c.id == job_id,
                        jobs.c.state == "dead",
                    )
                )
                .values(
                    state="pending",
                    attempts=0,
                    claimed_by=None,
                    claimed_at=None,
                    next_retry_at=None,
                    finished_at=None,
                    updated_at=now,
                )
            )

        return self.get_job(job_id)
    def recover_processing_jobs(self, timeout_seconds: int = 60):
        threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        now = datetime.utcnow()

        with engine.begin() as conn:
            recovered_ids = conn.execute(
                select(jobs.c.id)
                .select_from(
                    jobs.outerjoin(
                        workers,
                        jobs.c.claimed_by == workers.c.worker_id,
                    )
                )
                .where(
                    and_(
                        jobs.c.state == "processing",
                        or_(
                            workers.c.worker_id.is_(None),
                                workers.c.heartbeat.is_(None),
                            workers.c.heartbeat < threshold,
                        ),
                    )
                )
            ).scalars().all()

            if not recovered_ids:
                return []

            conn.execute(
                update(jobs)
                .where(
                    and_(
                        jobs.c.id.in_(recovered_ids),
                        jobs.c.state == "processing",
                    )
                )
                .values(
                    state="pending",
                    claimed_by=None,
                    claimed_at=None,
                    updated_at=now,
                )
            )

            return recovered_ids

    def get_job(self, job_id: int):
        with engine.connect() as conn:
            return conn.execute(
                select(jobs)
                .where(jobs.c.id == job_id)
            ).mappings().first()

    def list_jobs(self, state=None):
        with engine.connect() as conn:

            query = select(jobs)

            if state:
                query = query.where(jobs.c.state == state)

            query = query.order_by(jobs.c.created_at)

            return conn.execute(query).mappings().all()

    def get_all_jobs(self):
        return self.list_jobs()

    def get_pending_jobs(self):
        return self.list_jobs("pending")

    def get_processing_jobs(self):
        return self.list_jobs("processing")

    def get_completed_jobs(self):
        return self.list_jobs("completed")

    def get_failed_jobs(self):
        return self.list_jobs("failed")

    def get_dead_jobs(self):
        return self.list_jobs("dead")

    def stats(self):
        with engine.connect() as conn:

            total = conn.execute(
                select(func.count())
                .select_from(jobs)
            ).scalar()

            pending = conn.execute(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.state == "pending")
            ).scalar()

            processing = conn.execute(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.state == "processing")
            ).scalar()

            completed = conn.execute(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.state == "completed")
            ).scalar()

            failed = conn.execute(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.state == "failed")
            ).scalar()

            dead = conn.execute(
                select(func.count())
                .select_from(jobs)
                .where(jobs.c.state == "dead")
            ).scalar()

            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "dead": dead,
            }