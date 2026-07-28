import argparse
import json

from queuectl.database.db import init_database
from queuectl.services.queue_service import QueueService
from queuectl.services.worker_service import WorkerService
from queuectl.repositories.config_repository import ConfigRepository

queue = QueueService()
workers = WorkerService()
config = ConfigRepository()


def enqueue(args):
    raw = " ".join(args.command).strip()

    if not raw:
        print("No command provided.")
        return

    # Try to parse the input as a JSON payload.
    # Expected shape: {"id": "...", "command": "...", "max_retries": N}
    # If it is not valid JSON, treat it as a plain command string (backward compat).
    job_id_label = None
    max_retries_override = None
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict) and "command" in payload:
            job_id_label = payload.get("id")
            max_retries_override = payload.get("max_retries")
            raw = payload["command"]
    except (json.JSONDecodeError, ValueError):
        pass

    if not raw:
        print("No command provided.")
        return

    job = queue.enqueue(raw, max_retries=max_retries_override)

    display_id = job_id_label if job_id_label is not None else job
    print(f"Job {display_id} queued (db id={job}).")


def worker_start(args):
    workers.start_and_wait(args.count)


def worker_stop(args):
    workers.stop()
    print("Stop signal sent to all workers.")


def status(args):
    stats = queue.status()

    print("\nQueue Status")
    print("-" * 35)
    print(f"Total Jobs     : {stats['total']}")
    print(f"Pending        : {stats['pending']}")
    print(f"Processing     : {stats['processing']}")
    print(f"Completed      : {stats['completed']}")
    print(f"Failed         : {stats['failed']}")
    print(f"Dead Letter    : {stats['dead']}")
    print(f"Active Workers : {workers.active()}")


def list_jobs(args):
    jobs = queue.list_jobs(args.state)

    if args.json:
        print(json.dumps([dict(job) for job in jobs], default=str, indent=2))
        return

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
            f"[{job['id']}] "
            f"{job['command']} "
            f"(attempts={job['attempts']})"
        )


def dlq_retry(args):
    if args.job_id is None:

        jobs = queue.list_jobs("dead")

        for job in jobs:
            queue.retry_dead(job["id"])

        print(f"Retried {len(jobs)} job(s).")

    else:
        queue.retry_dead(args.job_id)
        print(f"Retried job {args.job_id}.")


def config_get(args):
    rows = config.all()

    if not rows:
        print("No configuration found.")
        return

    for row in rows:
        print(f"{row['key']} = {row['value']}")


def config_set(args):
    config.set(args.key, args.value)
    print("Configuration updated.")
def build_parser():
    parser = argparse.ArgumentParser(
        prog="queuectl",
        description="QueueCTL - Distributed Job Queue"
    )

    sub = parser.add_subparsers(dest="command")

    # ------------------------
    # enqueue
    # ------------------------
    enqueue_parser = sub.add_parser(
        "enqueue",
        help="Enqueue a command"
    )

    enqueue_parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute"
    )

    enqueue_parser.set_defaults(func=enqueue)

    # ------------------------
    # worker
    # ------------------------
    worker_parser = sub.add_parser(
        "worker",
        help="Worker operations"
    )

    worker_sub = worker_parser.add_subparsers(dest="action")

    worker_start_parser = worker_sub.add_parser(
        "start",
        help="Start workers"
    )

    worker_start_parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of workers"
    )

    worker_start_parser.set_defaults(
        func=worker_start
    )

    worker_stop_parser = worker_sub.add_parser(
        "stop",
        help="Stop workers"
    )

    worker_stop_parser.set_defaults(
        func=worker_stop
    )

    # ------------------------
    # status
    # ------------------------
    status_parser = sub.add_parser(
        "status",
        help="Queue status"
    )

    status_parser.set_defaults(
        func=status
    )

    # ------------------------
    # list
    # ------------------------
    list_parser = sub.add_parser(
        "list",
        help="List jobs"
    )

    list_parser.add_argument(
        "--state",
        choices=[
            "pending",
            "processing",
            "completed",
            "failed",
            "dead",
        ],
        help="Filter by state",
    )

    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON",
    )

    list_parser.set_defaults(
        func=list_jobs
    )

    # ------------------------
    # dlq
    # ------------------------
    dlq_parser = sub.add_parser(
        "dlq",
        help="Dead Letter Queue"
    )

    dlq_sub = dlq_parser.add_subparsers(dest="action")

    dlq_list_parser = dlq_sub.add_parser(
        "list",
        help="List dead jobs"
    )

    dlq_list_parser.set_defaults(
        func=dlq_list
    )

    dlq_retry_parser = dlq_sub.add_parser(
        "retry",
        help="Retry dead jobs"
    )

    dlq_retry_parser.add_argument(
        "job_id",
        nargs="?",
        type=int,
        help="Retry specific job (optional)",
    )

    dlq_retry_parser.set_defaults(
        func=dlq_retry
    )

    # ------------------------
    # config
    # ------------------------
    config_parser = sub.add_parser(
        "config",
        help="Configuration"
    )

    config_sub = config_parser.add_subparsers(dest="action")

    config_get_parser = config_sub.add_parser(
        "get",
        help="Show configuration"
    )

    config_get_parser.set_defaults(
        func=config_get
    )

    config_set_parser = config_sub.add_parser(
        "set",
        help="Set configuration value"
    )

    config_set_parser.add_argument("key")
    config_set_parser.add_argument("value")

    config_set_parser.set_defaults(
        func=config_set
    )

    return parser


def main():
    init_database()
    config.initialize()

    parser = build_parser()

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()