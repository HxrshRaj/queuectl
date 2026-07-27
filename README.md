# QueueCTL

QueueCTL is a robust, lightweight, asynchronous job queue and worker pool system backed by SQLite and built with Python and SQLAlchemy Core.

## Features
- **Atomic Job Claiming:** Lock-free atomic state transitions prevent duplicate execution across multiple concurrent workers.
- **Resilience:** Built-in crash recovery mechanism automatically reclaims jobs from dead or unresponsive workers.
- **Exponential Backoff:** Configurable retry logic with exponential backoff for failing jobs before moving to a Dead Letter Queue (DLQ).
- **Graceful Shutdown:** Workers catch termination signals and complete their current in-flight job before exiting safely.
- **Independent Processes:** True concurrent execution using Python's `multiprocessing` to bypass the GIL.

## Architecture
- **No ORM:** Leverages raw SQLAlchemy Core for pure, explicit SQL queries and performance.
- **Repository Pattern:** Clean separation of concerns between Services (business logic), Repositories (database access), and Workers (execution loop).

## Usage
QueueCTL provides a simple CLI:

```bash
# Initialize DB and start 4 concurrent workers
python -m queuectl.main worker start 4

# Enqueue a job
python -m queuectl.main enqueue "echo Hello World"
python -m queuectl.main enqueue "python -c 'import time; time.sleep(5)'"

# Check status
python -m queuectl.main status

# List jobs
python -m queuectl.main list pending
```
