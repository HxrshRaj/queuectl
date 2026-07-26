import os
import time
import uuid
import subprocess

from queuectl.repositories.job_repository import JobRepository
from queuectl.repositories.worker_repository import WorkerRepository


class Worker:

    def __init__(self):

        self.job_repo = JobRepository()
        self.worker_repo = WorkerRepository()

        self.worker_id = str(uuid.uuid4())

        self.pid = os.getpid()

        self.running = True

        self.poll_interval = 1

    def start(self):

        self.worker_repo.register(
            self.worker_id,
            self.pid,
        )

        print(f"Worker {self.worker_id} started")

        try:

            while self.running:

                self.worker_repo.heartbeat(
                    self.worker_id,
                )

                self.job_repo.recover_processing_jobs()

                if self.worker_repo.should_stop(
                    self.worker_id,
                ):
                    break

                job = self.job_repo.claim_job(
                    self.worker_id,
                )

                if job is None:
                    time.sleep(
                        self.poll_interval,
                    )
                    continue

                self.execute_job(job)

        finally:

            self.worker_repo.unregister(
                self.worker_id,
            )

            print("Worker stopped")
    def execute_job(self, job):

        print(f"Executing Job #{job['id']}")

        try:

            result = subprocess.run(
                job["command"],
                shell=True,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:

                self.job_repo.mark_completed(
                    job["id"],
                )

                print(
                    f"Job #{job['id']} completed"
                )

            else:

                failed_job = self.job_repo.mark_failed(
                    job["id"],
                    result.stderr.strip()
                    if result.stderr
                    else f"Exit Code {result.returncode}",
                )

                self.job_repo.retry_job(
                    failed_job["id"],
                )

                print(
                    f"Job #{job['id']} failed"
                )

        except Exception as e:

            failed_job = self.job_repo.mark_failed(
                job["id"],
                str(e),
            )

            self.job_repo.retry_job(
                failed_job["id"],
            )

            print(
                f"Unexpected error while executing Job #{job['id']}"
            )