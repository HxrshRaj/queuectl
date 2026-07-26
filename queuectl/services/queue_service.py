from queuectl.repositories.job_repository import JobRepository


class QueueService:

    def __init__(self):
        self.jobs = JobRepository()

    def enqueue(self, command: str):
        return self.jobs.enqueue(command)

    def list_jobs(self, state=None):
        return self.jobs.list_jobs(state)

    def status(self):
        return self.jobs.stats()

    def retry_dead(self, job_id: int):
        return self.jobs.retry_dead_job(job_id)