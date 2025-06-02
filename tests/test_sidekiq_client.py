import time
import json
import pytest
import re
import redis
from sidekiq_client import SidekiqClient


@pytest.fixture(scope="module")
def redis_client():
    client = redis.Redis.from_url("redis://redis:6379/0") # type: ignore
    client.flushdb() # type: ignore
    return client


@pytest.fixture(autouse=True)
def cleanup_redis(redis_client): # type: ignore
    redis_client.flushdb() # type: ignore
    yield
    redis_client.flushdb() # type: ignore


@pytest.fixture
def sidekiq(redis_client): # type: ignore
    return SidekiqClient(redis_client) # type: ignore


def assert_jid_format(jid: str):
    assert isinstance(jid, str)
    assert len(jid) == 24
    assert re.fullmatch(r"[0-9a-f]{24}", jid)


def test_perform_async_enqueues_job(sidekiq, redis_client): # type: ignore
    queue = "default"
    job_class = "MyWorker"
    args = [1, 2, 3]

    count = sidekiq.perform_async(queue, job_class, args) # type: ignore

    assert count == 1
    assert redis_client.llen(f"queue:{queue}") == 1 # type: ignore

    raw_job = redis_client.lpop(f"queue:{queue}") # type: ignore
    job = json.loads(raw_job) # type: ignore

    assert job["class"] == job_class
    assert job["queue"] == queue
    assert job["args"] == args
    assert "created_at" in job
    assert "enqueued_at" in job
    assert_jid_format(job["jid"])


def test_perform_in_adds_scheduled_job(sidekiq, redis_client): # type: ignore
    queue = "delayed"
    job_class = "DelayedJob"
    args = ["x"]
    seconds = 60

    sidekiq.perform_in(seconds, queue, job_class, args) # type: ignore

    assert redis_client.zcard("schedule") == 1 # type: ignore

    job_data, score = redis_client.zrange("schedule", 0, 0, withscores=True)[0] # type: ignore
    job = json.loads(job_data) # type: ignore

    assert job["class"] == job_class
    assert job["queue"] == queue
    assert job["args"] == args
    assert "created_at" in job
    assert "enqueued_at" not in job
    assert_jid_format(job["jid"])
    assert abs(score - (time.time() + seconds)) < 5 # type: ignore


def test_perform_at_adds_job_at_exact_time(sidekiq, redis_client): # type: ignore
    queue = "scheduled"
    job_class = "SpecificTimeJob"
    args = ["run_at"]
    timestamp = time.time() + 120

    sidekiq.perform_at(timestamp, queue, job_class, args, retry=False) # type: ignore

    assert redis_client.zcard("schedule") == 1 # type: ignore

    job_data, score = redis_client.zrange("schedule", 0, 0, withscores=True)[0] # type: ignore
    job = json.loads(job_data) # type: ignore

    assert job["class"] == job_class
    assert job["queue"] == queue
    assert job["args"] == args
    assert job["retry"] is False
    assert "created_at" in job
    assert "enqueued_at" not in job
    assert_jid_format(job["jid"])
    assert abs(score - timestamp) < 1 # type: ignore
