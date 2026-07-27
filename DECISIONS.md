# Design Decisions

This document explains the core architectural decisions made in QueueCTL.

## 1. Database: SQLite + SQLAlchemy Core
**Decision:** Use SQLite with SQLAlchemy Core (no ORM).
**Rationale:** SQLite provides a zero-configuration, file-based database ideal for this assignment. SQLAlchemy Core allows us to build programmatic, parameterized SQL queries while avoiding the overhead and "magic" of an ORM. We use `check_same_thread=False` and rely on SQLite's deferred transactions.

## 2. Atomicity & Locking
**Decision:** Lock-free atomic updates for job claiming.
**Rationale:** Instead of using explicit locks (which can cause deadlocks in SQLite), we use atomic `UPDATE jobs SET state='processing' WHERE id=X AND state='pending'`. The database enforces that only one worker can successfully flip the state.

## 3. Worker Concurrency
**Decision:** Use `multiprocessing` instead of `threading` or `asyncio`.
**Rationale:** To execute arbitrary blocking shell commands safely without freezing the heartbeat loop or being constrained by the GIL, we run workers in entirely separate processes. Each worker has a daemon thread dedicated solely to updating its heartbeat in the DB.

## 4. Crash Recovery
**Decision:** Heartbeat-based stale job recovery.
**Rationale:** A worker could be abruptly killed (OOM, SIGKILL) without running its cleanup block. The recovery manager looks for jobs in the `processing` state where the assigned worker's heartbeat is older than the `recovery-timeout`, resetting them to `pending`.
