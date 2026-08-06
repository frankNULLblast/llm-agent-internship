#!/usr/bin/env python3
"""Consume at most one event and ACK only after the MySQL commit."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from typing import Any

import mysql.connector
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


def validate_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("message body must be a JSON object")

    required_string_fields = ("event_id", "intern_name", "event_type")
    for field in required_string_fields:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f"{field} must be a non-empty string")

    uuid.UUID(value["event_id"])

    if not isinstance(value.get("payload"), dict):
        raise ValueError("payload must be a JSON object")

    return value


def open_database() -> mysql.connector.MySQLConnection:
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=required_env("MYSQL_USER"),
        password=required_env("MYSQL_PASSWORD"),
        database=required_env("MYSQL_DATABASE"),
        autocommit=False,
        connection_timeout=10,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transaction-failure-test",
        action="store_true",
        help="force a duplicate-key error after the first insert is staged",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rabbit_connection = pika.BlockingConnection(rabbit_parameters())
    channel = rabbit_connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    method, _properties, body = channel.basic_get(
        queue=QUEUE_NAME,
        auto_ack=False,
    )

    if method is None:
        rabbit_connection.close()
        print("QUEUE_EMPTY")
        return 2

    database = None
    cursor = None

    try:
        event = validate_event(json.loads(body.decode("utf-8")))
        payload_json = json.dumps(
            event["payload"],
            ensure_ascii=False,
            separators=(",", ":"),
        )

        database = open_database()
        cursor = database.cursor()
        database.start_transaction()
        row_values = (
            event["event_id"],
            event["intern_name"],
            event["event_type"],
            payload_json,
        )
        cursor.execute(
            """
            INSERT INTO lab_events (
              event_id,
              intern_name,
              event_type,
              payload
            )
            VALUES (%s, %s, %s, %s)
            AS new
            ON DUPLICATE KEY UPDATE event_id = new.event_id
            """,
            row_values,
        )
        if args.transaction_failure_test:
            cursor.execute(
                """
                INSERT INTO lab_events (
                  event_id,
                  intern_name,
                  event_type,
                  payload
                )
                VALUES (%s, %s, %s, %s)
                """,
                row_values,
            )
        database.commit()
    except Exception as exc:
        if database is not None and database.is_connected():
            database.rollback()
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,
        )
        print(
            f"PROCESSING_FAILED: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)
        result = "inserted" if cursor.rowcount == 1 else "already_present"
        print(
            json.dumps(
                {
                    "result": result,
                    "event_id": event["event_id"],
                    "acknowledged": True,
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        if cursor is not None:
            cursor.close()
        if database is not None and database.is_connected():
            database.close()
        if rabbit_connection.is_open:
            rabbit_connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
