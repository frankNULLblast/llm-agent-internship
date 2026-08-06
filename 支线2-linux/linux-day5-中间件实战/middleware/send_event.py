#!/usr/bin/env python3
"""Publish one persistent event to the durable linux.events queue."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import datetime, timezone

import pika

QUEUE_NAME = "linux.events"


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def rabbit_parameters() -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(
        required_env("RABBITMQ_DEFAULT_USER"),
        required_env("RABBITMQ_DEFAULT_PASS"),
        erase_on_connect=True,
    )
    return pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "127.0.0.1"),
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        virtual_host="/",
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
        connection_attempts=5,
        retry_delay=2,
        socket_timeout=10,
        stack_timeout=15,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--malformed-test",
        action="store_true",
        help="publish invalid JSON for the controlled failure exercise",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message_id = str(uuid.uuid4())

    if args.malformed_test:
        body = b'{"event_id": invalid-json'
        output_label = "MALFORMED_TEST_SENT"
    else:
        event = {
            "event_id": message_id,
            "intern_name": "intern",
            "event_type": "linux.lab.completed",
            "payload": {
                "course": "linux-five-day-lab",
                "source": "rabbitmq",
                "day": 5,
            },
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        output_label = "EVENT_SENT"

    connection = pika.BlockingConnection(rabbit_parameters())
    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=2,
                message_id=message_id,
                timestamp=int(datetime.now(timezone.utc).timestamp()),
            ),
            mandatory=True,
        )
    finally:
        if connection.is_open:
            connection.close()

    print(
        json.dumps(
            {
                "result": output_label,
                "queue": QUEUE_NAME,
                "message_id": message_id,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
