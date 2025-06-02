# python-sidekiq-client

Redis client for dispatching Sidekiq jobs from Python.

## Description

`python-sidekiq-client` lets you enqueue jobs into Redis in the same format Sidekiq expects. It provides:
- `perform_async`: push a job for immediate processing
- `perform_in`: schedule a job after a delay
- `perform_at`: schedule a job at a specific Unix timestamp

All payloads follow Sidekiq’s JSON schema:
```json
{
  "class": "YourWorkerClass",
  "queue": "default",
  "args": [...],
  "jid": "randomhex",
  "created_at": 1234567890.123,
  "enqueued_at": 1234567890.123,
  // plus any extra options you pass (e.g., retry, backtrace)
}
```

## Installation

If published to PyPI:
```bash
pip install python-sidekiq-client
```

## Usage

### 1. Initialize the Client

```python
from sidekiq_client import SidekiqClient

# Option A: pass Redis URL
client = SidekiqClient("redis://localhost:6379/0")

# Option B: pass existing Redis instance
from redis import Redis
redis_conn = Redis(host="localhost", port=6379, db=0)
client = SidekiqClient(redis_conn)
```

### 2. Enqueue a Job Immediately

```python
jid = client.perform_async(
    queue="default",
    job_class="EmailWorker",
    args=[{"to": "user@example.com", "subject": "Welcome"}],
    retry=False
)
print(f"Enqueued job with JID: {jid}")
```
- Returns the result of `LPUSH` (new length of `queue:default`).

### 3. Schedule a Job After a Delay

```python
# Schedule to run in 30 seconds
client.perform_in(
    seconds_from_now=30,
    queue="low_priority",
    job_class="CleanupWorker",
    args=[{"folder": "/tmp/cache"}],
    retry=True
)
```
- Adds the job payload to sorted set `schedule` with score = now + 30.

### 4. Schedule a Job at a Specific Time

```python
import time

run_at = time.mktime((2025, 6, 10, 10, 0, 0, 0, 0, 0))
client.perform_at(
    unix_timestamp=run_at,
    queue="reports",
    job_class="DailyReportWorker",
    args=[{"report_date": "2025-06-09"}],
    retry=False
)
```
- Adds to `schedule` set with score = `run_at`.

## API Reference

### `SidekiqClient(redis: Union[str, Redis])`

- `redis`: Redis URL string (`"redis://host:port/db"`) or a `redis.Redis` instance.
- Internally calls `Redis.from_url` if a string is provided.

### `perform_async(queue: str, job_class: str, args: List[Any], **options) -> str`

- `queue`: Redis list name (e.g. `"default"`).
- `job_class`: Worker class name as a string.
- `args`: List of JSON-serializable arguments.
- `**options`: Any extra keys added to the payload (e.g., `retry`, `backtrace`, `tags`).
- Returns the job's id

### `perform_in(seconds_from_now: int, queue: str, job_class: str, args: List[Any], **options) -> str`

- `seconds_from_now`: Delay in seconds before job is eligible.
- Other parameters as in `perform_async`.
- Adds JSON payload (without `"enqueued_at"`) to `schedule` sorted set.
- Returns the job's id

### `perform_at(unix_timestamp: float, queue: str, job_class: str, args: List[Any], **options) -> str`

- `unix_timestamp`: Exact Unix time when job should run.
- Other parameters as in `perform_async`.
- Adds to `schedule` set with given score.
- Returns the job's id

## Examples

```python
import time
from sidekiq_client import SidekiqClient

client = SidekiqClient("redis://localhost:6379/0")

# 1. Immediate job
jid = client.perform_async(
    queue="default",
    job_class="EmailWorker",
    args=[{"to": "user@example.com"}],
    retry=False
)
print(f"JID={jid}")

# 2. Schedule in 10 seconds
client.perform_in(
    seconds_from_now=10,
    queue="notifications",
    job_class="PushNotifWorker",
    args=[{"user_id": 42}]
)

# 3. Schedule at fixed time
target = time.mktime((2025,6,5,15,0,0,0,0,0))
client.perform_at(
    unix_timestamp=target,
    queue="reports",
    job_class="GenerateReportWorker",
    args=[{"report_id":101}],
    retry=False
)
```

## Running Tests

1. Ensure Redis is running on localhost:6379
2. Install `pytest`:
   ```bash
   pip install pytest
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Contributing

1. Fork repository
2. Create a branch
3. Commit changes:
4. Push branch and open a Pull Request.

Please include tests and keep changes focused.

## License

See [LICENSE](LICENSE.md) for details.