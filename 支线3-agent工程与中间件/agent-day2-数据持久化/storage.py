import os
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from typing import Iterator
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


RUN_STATUSES = (
    "enqueue_failed",
    "queued",
    "running",
    "waiting_review",
    "succeeded",
    "rejected",
    "failed",
)
TERMINAL_STATUSES = frozenset({"succeeded", "rejected", "failed"})


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('enqueue_failed','queued','running','waiting_review',"
            "'succeeded','rejected','failed')",
            name="ck_agent_runs_status",
        ),
        Index("ix_agent_runs_status_created", "status", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="enqueue_failed")
    payload_json: Mapped[dict] = mapped_column(JSONB)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    current_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class AgentRunEvent(Base):
    __tablename__ = "agent_run_events"
    __table_args__ = (Index("ix_agent_run_events_run_id_id", "run_id", "id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
    )
    event_type: Mapped[str] = mapped_column(String(64))
    request_id: Mapped[str] = mapped_column(String(64))
    detail_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


def database_url() -> str:
    value = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not value:
        raise RuntimeError("未设置 SQLALCHEMY_DATABASE_URL")
    return value


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    # 延迟建引擎：导入本模块不应要求数据库在线，否则旧接口的离线测试会失败。
    return create_engine(
        database_url(),
        pool_size=2,
        max_overflow=0,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_event(
    session: Session,
    run_id: UUID,
    event_type: str,
    request_id: str,
    detail: dict | None = None,
) -> None:
    session.add(
        AgentRunEvent(
            run_id=run_id,
            event_type=event_type,
            request_id=request_id,
            detail_json=detail or {},
        )
    )


def run_to_dict(run: AgentRun) -> dict:
    return {
        "run_id": run.id,
        "status": run.status,
        "result": run.result_json,
        "model_usage": run.model_usage,
        "error_code": run.error_code,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }
