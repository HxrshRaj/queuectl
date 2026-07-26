from datetime import datetime

from sqlalchemy import insert

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
        raise NotImplementedError

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