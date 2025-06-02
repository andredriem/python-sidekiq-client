"""Redis client for Sidekiq-like Job Processing.

This module provides a RedisClient class that enables asynchronous job
scheduling and execution using Redis.
"""

import time
import json
import secrets
from typing import Union, Any, List, Dict
from redis import Redis


class SidekiqClient:
    """Sidekiq client for dispatching jobs to Redis.

    This client connects to a Redis server and supports both immediate and
    scheduled job processing.
    """

    def __init__(self, redis: Union[str, Redis]) -> None:
        """Initialize the SidekiqClient.

        Args:
            redis: Either a Redis connection URL (str) or a Redis instance.
        """
        if isinstance(redis, str):
            self.redis = Redis.from_url(redis) # type: ignore
        else:
            self.redis = redis

    def perform_async(
        self, queue: str, job_class: str, args: List[Any], **options: Any
    ) -> str:
        """Enqueue a job for immediate asynchronous processing.

        Args:
            queue: Name of the queue.
            job_class: Name of the job class.
            args: List of arguments for the job.
            **options: Additional options to include in the job payload.
        """
        job = self._build_job_payload(queue, job_class, args, options)
        self.redis.lpush(f"queue:{queue}", json.dumps(job))
        return job["jid"]

    def perform_in(
        self,
        seconds_from_now: int,
        queue: str,
        job_class: str,
        args: List[Any],
        **options: Any,
    ) -> str:
        """Schedule a job to run after a certain delay.

        Args:
            seconds_from_now: Delay in seconds before the job should run.
            queue: Name of the queue.
            job_class: Name of the job class.
            args: List of arguments for the job.
            **options: Additional options to include in the job payload.
        """
        timestamp = time.time() + seconds_from_now
        return self._zadd_scheduled(queue, job_class, args, timestamp, options)

    def perform_at(
        self,
        unix_timestamp: float,
        queue: str,
        job_class: str,
        args: List[Any],
        **options: Any,
    ) -> str:
        """Schedule a job to run at a specific Unix timestamp.

        Args:
            queue: Name of the queue.
            job_class: Name of the job class.
            args: List of arguments for the job.
            unix_timestamp: Unix timestamp when the job should run.
            **options: Additional options to include in the job payload.
        """
        return self._zadd_scheduled(queue, job_class, args, unix_timestamp, options)

    def _zadd_scheduled(
        self,
        queue: str,
        job_class: str,
        args: List[Any],
        timestamp: float,
        options: Dict[str, Any],
    ) -> str:
        """Add a scheduled job to the Redis sorted set.

        Args:
            queue: Name of the queue.
            job_class: Name of the job class.
            args: List of arguments for the job.
            timestamp: Unix timestamp when the job is scheduled.
            options: Additional options to include in the job payload.
        """
        job = self._build_job_payload(queue, job_class, args, options,
                                      enqueued_at=False)
        self.redis.zadd("schedule", {json.dumps(job): timestamp})
        return job["jid"]

    def _build_job_payload(
        self,
        queue: str,
        job_class: str,
        args: List[Any],
        options: Dict[str, Any],
        enqueued_at: bool = True,
    ) -> Dict[str, Any]:
        """Build the job payload.

        Args:
            queue: Name of the queue.
            job_class: Name of the job class.
            args: List of arguments for the job.
            options: Additional options to include in the job payload.
            enqueued_at: Whether to include the enqueued timestamp. Defaults to True.

        Returns:
            A dictionary representing the job payload.
        """
        now = time.time()
        job: Dict[str, Any] = {
            "class": job_class,
            "queue": queue,
            "args": args,
            "jid": secrets.token_hex(12),
            "created_at": now,
        }

        if enqueued_at:
            job["enqueued_at"] = now

        # Merge any additional options (e.g., retry settings, metadata)
        job.update(options)
        return job
