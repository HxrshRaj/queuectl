# Design Decisions

This document explains the key architectural and implementation decisions made while developing **QueueCTL**. The focus was to build a reliable, maintainable, and fault-tolerant command-line job queue while satisfying the assignment requirements.

---

# 1. SQLite as the Storage Backend

SQLite was selected as the persistent storage engine because it satisfies the assignment requirements while keeping deployment simple.

### Reasons

- Zero configuration
- Embedded database
- ACID-compliant transactions
- Reliable persistence
- Lightweight and portable
- Sufficient concurrency for a local job queue

### Trade-off

SQLite does not provide the same write concurrency as client-server databases such as PostgreSQL. However, for the expected workload of QueueCTL, it provides an excellent balance between simplicity and reliability.

---

# 2. SQLAlchemy Core Instead of ORM

The project uses **SQLAlchemy Core** rather than the SQLAlchemy ORM.

### Reasons

- Explicit SQL statements
- Better control over transactions
- Lower abstraction
- Easier implementation of atomic updates
- Complies with the assignment requirement

Using SQLAlchemy Core keeps database interactions transparent while avoiding unnecessary ORM complexity.

---

# 3. Repository Pattern

All database operations are isolated within repository classes.

Repositories include:

- JobRepository
- WorkerRepository
- ConfigRepository

### Benefits

- Clear separation of concerns
- Reusable database logic
- Easier testing
- Business logic remains independent of SQL
- Simplifies future database changes

---

# 4. Service Layer

Business logic is implemented inside services rather than the CLI.

The CLI is responsible only for:

- Parsing commands
- Validating user input
- Displaying output

The Service Layer manages:

- Queue operations
- Retry policy
- Worker orchestration
- Configuration management

This keeps the command-line interface lightweight while centralizing application logic.

---

# 5. Worker Architecture

Workers execute independently and continuously poll the queue for eligible jobs.

Each worker is responsible for:

- Claiming jobs
- Executing shell commands
- Updating job state
- Sending heartbeat updates
- Handling retries
- Recovering abandoned jobs during startup

Keeping workers independent simplifies scaling by allowing additional worker processes to be started whenever higher throughput is required.

---

# 6. Atomic Job Claiming

Preventing duplicate execution is one of the most important requirements.

Jobs are claimed using an atomic database transaction that succeeds only if the job is still in the `pending` state.

This guarantees:

- One worker claims a job
- Multiple workers cannot execute the same job simultaneously
- Exactly-once execution under normal operation

---

# 7. Retry Strategy

Transient failures should not immediately move jobs to the Dead Letter Queue.

The retry workflow is:

1. Increment the attempt counter
2. Record the execution error
3. Compute the next retry time
4. Return the job to the pending queue

Once the configured retry limit is reached, the job is moved to the Dead Letter Queue.

---

# 8. Exponential Backoff

Retries use exponential backoff.

```
delay = backoff_base ^ attempts
```

### Benefits

- Prevents rapid retry loops
- Reduces unnecessary resource usage
- Gives external systems time to recover
- Avoids repeatedly executing failing commands

The retry behavior can be adjusted through runtime configuration without modifying the source code.

---

# 9. Dead Letter Queue (DLQ)

Jobs that exceed the configured retry limit are retained instead of being deleted.

### Advantages

- Preserves failure history
- Enables manual inspection
- Supports manual retry
- Prevents silent data loss

This improves observability while allowing failed jobs to be recovered later if appropriate.

---

# 10. Worker Heartbeats

Each worker periodically updates a heartbeat timestamp in the database while running.

Heartbeats allow the system to distinguish between:

- Healthy workers
- Gracefully stopped workers
- Unexpectedly crashed workers

Heartbeat updates continue even while long-running jobs are executing, enabling accurate failure detection.

---

# 11. Crash Recovery

Unexpected worker termination should not permanently block queued work.

When a worker starts, it performs a recovery pass that:

- Finds jobs left in the `processing` state
- Detects stale or missing workers using heartbeat timestamps
- Returns abandoned jobs to the `pending` state

Recovered jobs are then processed normally by active workers.

---

# 12. Runtime Configuration

QueueCTL stores runtime configuration in the database rather than hardcoding operational values.

Current configurable settings include:

- max-retries
- backoff-base
- poll-interval
- recovery-timeout

This allows operational behavior to be modified without changing application code.

---

# 13. Graceful Shutdown

Workers respond to shutdown signals by:

- Stopping new job acquisition
- Finishing the current job
- Updating worker status
- Unregistering cleanly
- Exiting normally

This minimizes inconsistent job states and avoids interrupting active work.

---

# 14. Logging

The Python `logging` module provides operational visibility throughout the system.

Logged events include:

- Worker lifecycle
- Job execution
- Retry scheduling
- Dead Letter Queue transitions
- Recovery events
- Execution failures

These logs simplify debugging and monitoring during development.

---

# 15. Error Handling

Execution failures are captured and stored with the associated job.

Recorded information includes:

- Execution attempts
- Error messages
- Final failure reason
- Dead Letter Queue transitions

Maintaining execution history improves troubleshooting while supporting reliable retry behavior.

---

# 16. Overall Architecture

QueueCTL follows a layered architecture.

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

### Design Goals

The architecture emphasizes:

- Simplicity
- Reliability
- Separation of concerns
- Transactional correctness
- Fault tolerance
- Recoverability
- Maintainability
- Extensibility

Each layer has a single, well-defined responsibility, making the system easier to understand, test, and extend while preserving clear boundaries between user interaction, business logic, and persistence.
