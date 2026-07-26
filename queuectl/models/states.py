from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class WorkerState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"