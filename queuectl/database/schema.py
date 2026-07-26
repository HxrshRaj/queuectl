from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Table,
    Text,
)

from queuectl.database.db import metadata


jobs = Table(
    "jobs",
    metadata,

    Column("id", Integer, primary_key=True, autoincrement=True),

    Column("command", Text, nullable=False),

    Column("state", String(20), nullable=False),

    Column("attempts", Integer, nullable=False, default=0),

    Column("max_retries", Integer, nullable=False, default=3),

    Column("next_retry_at", DateTime),

    Column("claimed_by", String(64)),

    Column("claimed_at", DateTime),

    Column("last_error", Text),

    Column("created_at", DateTime, nullable=False),

    Column("updated_at", DateTime, nullable=False),

    Column("finished_at", DateTime),
)


workers = Table(
    "workers",
    metadata,

    Column("worker_id", String(64), primary_key=True),

    Column("pid", Integer, nullable=False),

    Column("status", String(20), nullable=False),

    Column("heartbeat", DateTime),

    Column("started_at", DateTime),

    Column("stop_requested", Boolean, nullable=False, default=False),
)


config = Table(
    "config",
    metadata,

    Column("key", String(64), primary_key=True),

    Column("value", String(255), nullable=False),
)