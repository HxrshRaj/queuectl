from queuectl.repositories.job_repository import JobRepository
from queuectl.repositories.config_repository import ConfigRepository


class RecoveryManager:

    def __init__(self):
        self.jobs = JobRepository()
        self.config = ConfigRepository()

    def recover(self):
        timeout = self.config.get_int("recovery-timeout")

        if timeout is None:
            timeout = 60

        return self.jobs.recover_processing_jobs(timeout)