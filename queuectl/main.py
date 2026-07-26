import argparse
from queuectl.services.queue_service import QueueService
from queuectl.services.worker_service import WorkerService
from queuectl.repositories.config_repository import ConfigRepository


queue = QueueService()
workers = WorkerService()
config = ConfigRepository()


def enqueue(args):
    job = queue.enqueue(args.command)
    print(f"Job {job} queued.")


def worker_start(args):
    workers.start(args.count)
    print(f"Started {args.count} worker(s).")


def worker_stop(args):
    workers.stop()
    print("Stop signal sent to all workers.")


def status(args):
    stats = queue.status()

    print(f"Total      : {stats['total']}")
    print(f"Pending    : {stats['pending']}")
    print(f"Processing : {stats['processing']}")
    print(f"Completed  : {stats['completed']}")
    print(f"Failed     : {stats['failed']}")
    print(f"Dead       : {stats['dead']}")
    print(f"Workers    : {workers.active()}")


def list_jobs(args):
    jobs = queue.list_jobs(args.state)

    if not jobs:
        print("No jobs found.")
        return

    for job in jobs:
        print(
            f"[{job['id']}] "
            f"{job['state']} "
            f"attempts={job['attempts']} "
            f"{job['command']}"
        )


def dlq_list(args):
    jobs = queue.list_jobs("dead")

    if not jobs:
        print("Dead letter queue empty.")
        return

    for job in jobs:
        print(
            f"[{job['id']}] {job['command']}"
        )


def dlq_retry(args):
    queue.retry_dead(args.job_id)
    print("Job moved back to queue.")


def config_set(args):
    config.set(args.key, args.value)
    print("Configuration updated.")
def build_parser():
    parser = argparse.ArgumentParser(prog="queuectl")

    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("enqueue")
    p.add_argument("command")
    p.set_defaults(func=enqueue)

    worker = sub.add_parser("worker")
    worker_sub = worker.add_subparsers(dest="action")

    ws = worker_sub.add_parser("start")
    ws.add_argument("--count", type=int, default=1)
    ws.set_defaults(func=worker_start)

    wt = worker_sub.add_parser("stop")
    wt.set_defaults(func=worker_stop)

    st = sub.add_parser("status")
    st.set_defaults(func=status)

    ls = sub.add_parser("list")
    ls.add_argument(
        "--state",
        choices=[
            "pending",
            "processing",
            "completed",
            "failed",
            "dead",
        ],
    )
    ls.set_defaults(func=list_jobs)

    dlq = sub.add_parser("dlq")
    dlq_sub = dlq.add_subparsers(dest="action")

    l = dlq_sub.add_parser("list")
    l.set_defaults(func=dlq_list)

    r = dlq_sub.add_parser("retry")
    r.add_argument("job_id", type=int)
    r.set_defaults(func=dlq_retry)

    cfg = sub.add_parser("config")
    cfg_sub = cfg.add_subparsers(dest="action")

    s = cfg_sub.add_parser("set")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(func=config_set)

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()