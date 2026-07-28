# QueueCTL

QueueCTL is a lightweight command-line job queue system built in Python that allows users to enqueue shell commands, process them asynchronously using one or more worker processes, automatically retry failed jobs with exponential backoff, and recover interrupted work after unexpected worker crashes.

The project follows a clean layered architecture based on the **Repository Pattern** using **SQLAlchemy Core** with **SQLite** as the persistent storage backend.

---

# Features

- Command-line interface (CLI)
- Persistent SQLite-backed job queue
- JSON-based job submission
- Multiple concurrent worker processes
- Atomic job claiming
- Exactly-once job execution
- Automatic retries
- Configurable exponential backoff
- Dead Letter Queue (DLQ)
- Worker heartbeat monitoring
- Automatic crash recovery
- Graceful worker shutdown
- Runtime configuration management
- Repository Pattern architecture
- SQLAlchemy Core (No ORM)

---

# Project Structure

```
queuectl/
│
├── database/
│   ├── engine.py
│   └── schema.py
│
├── repositories/
│   ├── job_repository.py
│   ├── worker_repository.py
│   └── config_repository.py
│
├── services/
│   ├── queue_service.py
│   └── worker_service.py
│
├── workers/
│   ├── worker.py
│   ├── executor.py
│   └── recovery.py
│
├── utils/
│
└── main.py
```

---

# Architecture

QueueCTL follows a layered architecture that separates business logic from persistence and command execution.

```
           CLI
            │
            ▼
     Service Layer
            │
            ▼
   Repository Layer
            │
            ▼
     SQLite Database
```

### Responsibilities

### CLI

- Parses user commands
- Validates input
- Displays output

### Service Layer

- Business logic
- Queue operations
- Worker orchestration

### Repository Layer

- Database transactions
- Atomic job claiming
- Configuration persistence
- Worker heartbeat management

### Worker Layer

- Executes shell commands
- Handles retries
- Updates job state
- Sends heartbeats
- Performs crash recovery

---

# Database Schema

## Jobs

| Column | Description |
|---------|-------------|
| id | Database job identifier |
| command | Shell command |
| state | pending / processing / completed / dead |
| attempts | Retry attempts |
| max_retries | Maximum retries |
| next_retry_at | Next eligible execution time |
| claimed_by | Worker UUID |
| claimed_at | Timestamp when claimed |
| last_error | Most recent execution error |
| created_at | Creation timestamp |
| updated_at | Last modification |
| finished_at | Completion timestamp |

---

## Workers

| Column | Description |
|---------|-------------|
| worker_id | Worker UUID |
| pid | Operating system process ID |
| status | running / stopped |
| heartbeat | Last heartbeat timestamp |
| started_at | Worker startup time |
| stop_requested | Graceful shutdown flag |

---

## Config

Simple key-value table storing runtime configuration.

Available settings include:

- max-retries
- backoff-base
- poll-interval
- recovery-timeout

---

# Installation

Clone the repository.

```bash
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate the environment.

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# Usage

## Enqueue a Job

```bash
queuectl enqueue '{"id":"job1","command":"echo Hello World"}'
```

---

## Start a Worker

```bash
queuectl worker start
```

---

## List Jobs

```bash
queuectl list
```

Filter by state:

```bash
queuectl list --state pending
```

Return JSON:

```bash
queuectl list --json
```

---

## Queue Status

```bash
queuectl status
```

---

## Dead Letter Queue

View failed jobs:

```bash
queuectl dlq list
```

Retry a dead job:

```bash
queuectl dlq retry <job-id>
```

---

## Configuration

Display all configuration values.

```bash
queuectl config get
```

Update a configuration value.

```bash
queuectl config set max-retries 5
```

Example:

```bash
queuectl config set backoff-base 2
```

---

# Example Workflow

### 1. Enqueue a job

```bash
queuectl enqueue '{"id":"hello","command":"echo Hello QueueCTL"}'
```

### 2. Start a worker

```bash
queuectl worker start
```

### 3. Check queue status

```bash
queuectl status
```

### 4. View completed jobs

```bash
queuectl list --state completed
```

---

# Retry Policy

If a job execution fails:

1. The retry counter is incremented.
2. The job is returned to the pending queue.
3. The next execution time is calculated using exponential backoff.

```
delay = backoff_base ^ attempts
```

For example, with:

```
backoff-base = 2
```

Retry delays become:

| Attempt | Delay |
|----------|------:|
| 1 | 2 seconds |
| 2 | 4 seconds |
| 3 | Job moved to DLQ |

Once the configured retry limit is reached, the job is moved to the Dead Letter Queue.

---

# Atomic Job Claiming

QueueCTL guarantees that multiple workers cannot execute the same job simultaneously.

Jobs are claimed atomically inside a database transaction before execution begins, ensuring exactly-once execution even when multiple workers are running concurrently.

---

# Dead Letter Queue (DLQ)

Jobs exceeding the retry limit are marked as **dead**.

Dead jobs remain stored for inspection and can later be retried using:

```bash
queuectl dlq retry <job-id>
```

---

# Worker Heartbeats

Each worker periodically updates its heartbeat in the database.

Heartbeats are used to determine whether a worker is still alive while processing long-running jobs.

---

# Crash Recovery

If a worker terminates unexpectedly:

1. The heartbeat stops updating.
2. The worker is considered stale after the configured `recovery-timeout`.
3. A new worker automatically detects abandoned jobs.
4. Interrupted jobs are safely returned to the pending queue.
5. The jobs are executed normally without duplication.

This allows QueueCTL to recover from unexpected worker crashes without losing queued work.

---

# Graceful Shutdown

Workers respond to termination signals by:

- stopping new job acquisition
- finishing the current job
- updating worker state
- unregistering themselves
- exiting cleanly

This prevents partially processed jobs from being left in an inconsistent state.

---

# Technologies Used

- Python 3
- SQLite
- SQLAlchemy Core
- argparse
- subprocess
- threading
- signal
- logging

---

# Design Principles

QueueCTL was designed with the following goals:

- Simplicity
- Reliability
- Recoverability
- Separation of concerns
- Transactional correctness
- Minimal dependencies
- Maintainability
- Extensibility

---

# Key Design Decisions

- SQLAlchemy Core is used instead of the ORM for explicit SQL queries and lightweight data access.
- SQLite provides a simple persistent backend suitable for a local job queue.
- The Repository Pattern separates persistence from business logic.
- Worker heartbeats enable reliable crash detection.
- Atomic database updates prevent duplicate execution across multiple workers.
- Runtime configuration allows retry behavior to be adjusted without code changes.

---

# License

This project was developed as part of a backend engineering assignment demonstrating concurrent job processing, fault tolerance, crash recovery, and layered software architecture.
