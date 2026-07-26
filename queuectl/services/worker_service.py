import multiprocessing

from queuectl.repositories.worker_repository import WorkerRepository
from queuectl.workers.worker import Worker


class WorkerService:

    def __init__(self):
        self.repo = WorkerRepository()

    def start(self, count=1):
        processes = []

        for _ in range(count):
            process = multiprocessing.Process(
                target=Worker.run,
            )

            process.daemon = False
            process.start()

            processes.append(process)

        return processes

    def stop(self):
        self.repo.request_stop_all()

    def workers(self):
        return self.repo.get_workers()

    def active(self):
        return self.repo.active_count()