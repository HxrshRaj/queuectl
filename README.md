# QueueCTL

QueueCTL is a lightweight command-line job queue system built in Python. It allows users to enqueue shell commands, execute them asynchronously using multiple worker processes, automatically retry failed jobs with exponential backoff, and recover work after unexpected worker crashes.

The project is designed around a clean layered architecture using the Repository Pattern and SQLAlchemy Core with SQLite.

---

## Features

- Command-line interface
- Persistent SQLite-backed queue
- Multiple worker processes
- Atomic job claiming
- Automatic retries
- Exponential backoff
- Dead Letter Queue (DLQ)
- Worker heartbeat monitoring
- Crash recovery
- Graceful shutdown
- Configurable retry settings
- Repository and Service layer architecture
- SQLAlchemy Core (No ORM)

---

## Project Structure

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

## Architecture

The application follows a layered architecture.

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

Responsibilities are separated as follows:

- CLI handles user interaction.
- Services contain business logic.
- Repositories manage database access.
- Workers execute jobs.
- Recovery logic restores interrupted work.

---

## Database Schema

### Jobs

| Column | Description |
|---------|-------------|
| id | Job identifier |
| command | Shell command |
| state | pending / processing / completed / failed / dead |
| attempts | Retry count |
| max_retries | Maximum retries |
| next_retry_at | Next eligible execution time |
| claimed_by | Worker ID |
| claimed_at | Claim timestamp |
| last_error | Last execution error |
| created_at | Creation time |
| updated_at | Last update |
| finished_at | Completion time |

### Workers

| Column | Description |
|---------|-------------|
| worker_id | Worker UUID |
| pid | Process ID |
| status | running / stopped |
| heartbeat | Last heartbeat |
| started_at | Worker start time |
| stop_requested | Shutdown flag |

### Config

Simple key-value configuration table.

---

## Installation

Clone the repository.

```bash
git clone <repository-url>
cd queuectl
```

Create a virtual environment.

```bash
python -m venv .venv
```

Activate it.

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

## Running

Initialize the database if required.

```bash
python -m queuectl.main init
```

Start workers.

```bash
python -m queuectl.main worker start --count 2
```

Enqueue a job.

```bash
python -m queuectl.main enqueue "echo Hello World"
```

List jobs.

```bash
python -m queuectl.main list
```

Check queue status.

```bash
python -m queuectl.main status
```

Stop workers.

```bash
python -m queuectl.main worker stop
```

---

## Retry Policy

When a job fails:

1. Attempts are incremented.
2. If retries remain, the job returns to the pending queue.
3. The next execution time is calculated using exponential backoff.
4. Once the retry limit is reached, the job is moved to the Dead Letter Queue.

---

## Dead Letter Queue

Jobs exceeding the retry limit are marked as `dead`.

Dead jobs remain stored until explicitly retried or inspected through the CLI.

---

## Worker Heartbeat

Each worker periodically updates its heartbeat timestamp in the database.

This allows the system to detect workers that terminate unexpectedly.

---

## Crash Recovery

On startup, the recovery manager checks for jobs stuck in the `processing` state.

Jobs owned by missing or stale workers are safely returned to the pending queue for re-execution.

---

## Graceful Shutdown

Workers respond to termination signals by:

- stopping new job acquisition
- completing the current job
- updating worker status
- exiting cleanly

This prevents partially executed jobs from being lost.

---

## Technologies

- Python
- SQLite
- SQLAlchemy Core
- multiprocessing
- argparse
- subprocess
- logging

---

## Design Goals

- Simplicity
- Reliability
- Recoverability
- Separation of concerns
- Easy maintenance
- Minimal external dependencies
