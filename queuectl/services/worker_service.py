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

            process.start()

            processes.append(process)

        return processes

    def start_and_wait(self, count=1):

        processes = self.start(count)

        try:
            for process in processes:
                process.join()

        except KeyboardInterrupt:
            self.stop()

            for process in processes:
                process.join()

    def stop(self):
        self.repo.request_stop_all()

    def workers(self):
        return self.repo.get_workers()

    def active(self):
        return self.repo.active_count()