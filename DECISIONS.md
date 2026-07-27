# Design Decisions

This document explains the major architectural decisions made during the implementation of QueueCTL.

---

# 1. SQLite

SQLite was selected because it satisfies the assignment requirements while keeping deployment simple.

Advantages:

- zero configuration
- embedded database
- transactional
- ACID compliant
- sufficient concurrency for this workload

---

# 2. SQLAlchemy Core

SQLAlchemy Core was chosen instead of the ORM.

Reasons:

- complies with the assignment constraint
- explicit SQL operations
- easier control over transactions
- lower abstraction
- easier implementation of atomic updates

---

# 3. Repository Pattern

All database operations are isolated inside repository classes.

Benefits:

- clean separation of concerns
- reusable queries
- easier testing
- services remain independent of SQL

Repositories include:

- JobRepository
- WorkerRepository
- ConfigRepository

---

# 4. Service Layer

Business logic is implemented inside services rather than the CLI.

Responsibilities include:

- queue operations
- retry handling
- worker management
- configuration management

The CLI only parses commands and delegates execution.

---

# 5. Multiprocessing

Workers are implemented using Python's multiprocessing module.

Reasons:

- true parallel execution
- avoids Python's GIL
- isolates worker failures
- supports long-running shell commands

---

# 6. Atomic Job Claiming

Preventing duplicate execution is essential.

Workers claim jobs using an atomic database update that succeeds only if the job is still pending.

This prevents multiple workers from processing the same job simultaneously.

---

# 7. Retry Strategy

Transient failures should not immediately move jobs to the Dead Letter Queue.

The retry workflow is:

- increment attempt count
- compute next retry time
- return job to pending state
- retry later

Permanent failures are moved to the DLQ after the configured retry limit.

---

# 8. Exponential Backoff

Retries use exponential backoff.

Benefits:

- reduces repeated failures
- prevents rapid retry loops
- decreases system load
- provides time for external dependencies to recover

---

# 9. Dead Letter Queue

Jobs that exceed the retry limit are retained rather than deleted.

Advantages:

- preserves failure history
- enables inspection
- supports manual retry
- avoids silent data loss

---

# 10. Worker Heartbeat

Each worker periodically updates a heartbeat timestamp.

The heartbeat allows the system to distinguish healthy workers from crashed workers.

---

# 11. Crash Recovery

During startup, recovery scans for jobs left in the processing state.

Jobs associated with missing or stale workers are returned to the pending queue.

This ensures interrupted work is not permanently lost.

---

# 12. Graceful Shutdown

Workers respond to shutdown signals by:

- stopping new work
- completing the active job
- updating worker status
- unregistering cleanly

This minimizes inconsistent job states.

---

# 13. Logging

The standard Python logging module is used for operational visibility.

Logging provides:

- execution history
- worker lifecycle events
- error reporting
- debugging information

---

# 14. Error Handling

Execution failures are captured and recorded.

Errors include:

- subprocess failures
- non-zero exit codes
- unexpected exceptions

Failure information is stored with each job to support retries and debugging.

---

# 15. Overall Architecture

The system follows a layered architecture:

```
CLI
    ↓
Service Layer
    ↓
Repository Layer
    ↓
SQLite Database
```

This separation improves maintainability, readability, and extensibility while keeping responsibilities clearly defined.
