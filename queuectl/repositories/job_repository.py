from queuectl.database.db import engine
from queuectl.database.schema import jobs


class JobRepository:
    def enqueue(self, command: str):
        raise NotImplementedError

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