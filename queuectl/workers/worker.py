import os
import signal
import time
import uuid
import threading

from queuectl.repositories.job_repository import JobRepository
from queuectl.repositories.worker_repository import WorkerRepository
from queuectl.repositories.config_repository import ConfigRepository
from queuectl.utils.executor import Executor
from queuectl.utils.recovery import RecoveryManager


class Worker:

    def __init__(self):
        self.worker_id = str(uuid.uuid4())
        self.pid = os.getpid()

        self.jobs = JobRepository()
        self.workers = WorkerRepository()
        self.config = ConfigRepository()
        self.executor = Executor()
        self.recovery = RecoveryManager()

        self.running = True

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signum=None, frame=None):
        self.running = False

    def _heartbeat_loop(self):
        poll_interval = self.config.get_int(
            "poll-interval"
        )

        if poll_interval is None:
            poll_interval = 1

        while self.running:
            self.workers.heartbeat(
                self.worker_id
            )
            time.sleep(poll_interval)

    def start(self):

        self.config.initialize()

        self.recover()

        self.workers.register(
            self.worker_id,
            self.pid,
        )

        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
        )
        heartbeat_thread.start()

        try:
            self.loop()

        finally:
            self.running = False

            if heartbeat_thread.is_alive():
                heartbeat_thread.join(timeout=2)

            try:
                self.workers.mark_stopped(
                    self.worker_id
                )
            finally:
                self.workers.unregister(
                    self.worker_id
                )

    def loop(self):

        poll_interval = self.config.get_int(
            "poll-interval"
        )

        if poll_interval is None:
            poll_interval = 1

        while self.running:

            if self.workers.should_stop(
                self.worker_id
            ):
                break

            self.workers.heartbeat(
                self.worker_id
            )

            job = self.jobs.claim_job(
                self.worker_id
            )

            if job is None:
                time.sleep(poll_interval)
                continue

            self.process_job(job)
    def process_job(self, job):

        try:
            result = self.executor.execute(
                job["command"]
            )

            if result.success:
                self.jobs.mark_completed(
                    job["id"]
                )

                print(
                    f"[{self.worker_id}] Job {job['id']} completed"
                )

                return

            self.handle_failure(
                job,
                result.stderr or f"Exit code {result.exit_code}",
            )

        except Exception as exc:
            self.handle_failure(
                job,
                str(exc),
            )

    def handle_failure(self, job, error):

        updated = self.jobs.mark_failed(
            job["id"],
            error,
        )

        if updated["attempts"] >= updated["max_retries"]:

            self.jobs.move_to_dead(
                updated["id"],
            )

            print(
                f"[{self.worker_id}] Job {updated['id']} moved to DLQ"
            )

            return

        self.jobs.retry_job(
            updated["id"]
        )

        print(
            f"[{self.worker_id}] Job {updated['id']} scheduled for retry ({updated['attempts']}/{updated['max_retries']})"
        )

    @classmethod
    def run(cls):
        worker = cls()
        worker.start()
    def recover(self):
        timeout = self.config.get_int("recovery-timeout")

        if timeout is None:
            timeout = 60

        recovered = self.jobs.recover_processing_jobs(timeout)

        if recovered:
            print(f"Recovered {len(recovered)} abandoned job(s).")

    def shutdown(self):
        try:
            self.workers.mark_stopped(self.worker_id)
        finally:
            self.workers.unregister(self.worker_id)

        print(f"Worker {self.worker_id} stopped.")

    @classmethod
    def run(cls):
        worker = cls()
        worker.start()