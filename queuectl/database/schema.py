from sqlalchemy import DateTime, Integer, String, Table, Text, Column

from queuectl.database.db import metadata


jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("command", Text, nullable=False),
    Column("state", String(20), nullable=False),
    Column("attempts", Integer, default=0),
    Column("max_retries", Integer, default=3),
    Column("next_retry_at", DateTime, nullable=True),
    Column("claimed_by", String(64), nullable=True),
    Column("claimed_at", DateTime, nullable=True),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

workers = Table(
    "workers",
    metadata,
    Column("worker_id", String(64), primary_key=True),
    Column("pid", Integer, nullable=True),
    Column("status", String(20), nullable=True),
    Column("heartbeat", DateTime, nullable=True),
    Column("started_at", DateTime, nullable=True),
)

config = Table(
    "config",
    metadata,
    Column("key", String(64), primary_key=True),
    Column("value", String(255), nullable=True),
)