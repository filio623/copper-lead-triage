import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, Index, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from backend.app.core.config import get_settings
from backend.app.models.analysis import (
    EnrichmentResult,
    LLMAnalysisResult,
    LeadAnalysisRecord,
    ReviewStatus,
    RuleScoreResult,
)
from backend.app.models.lead import NormalizedLead


RunType = Literal["sample", "bulk"]
RunStatus = Literal["pending", "running", "completed", "failed"]


class BatchRun(BaseModel):
    run_id: str
    run_type: RunType
    status: RunStatus = "pending"
    total_leads: int = 0
    processed_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LeadSnapshotRecord(BaseModel):
    snapshot_id: str
    copper_lead_id: int
    raw_payload: dict[str, Any]
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StoredLeadAnalysis(BaseModel):
    analysis_id: str
    copper_lead_id: int
    batch_run_id: Optional[str] = None
    raw_snapshot_id: Optional[str] = None
    normalized_lead: NormalizedLead
    rule_score: RuleScoreResult
    enrichment_result: Optional[EnrichmentResult] = None
    llm_analysis: Optional[LLMAnalysisResult] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_prompt_version: Optional[str] = None
    review_status: ReviewStatus = "pending"
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReviewDecision(BaseModel):
    review_id: str
    analysis_id: str
    decision: ReviewStatus
    notes: Optional[str] = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Base(DeclarativeBase):
    pass


class BatchRunORM(Base):
    __tablename__ = "batch_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    total_leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class LeadSnapshotORM(Base):
    __tablename__ = "lead_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    copper_lead_id: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[str] = mapped_column(String, nullable=False)


class LeadAnalysisORM(Base):
    __tablename__ = "lead_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    copper_lead_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    batch_run_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("batch_runs.id"),
        nullable=True,
        index=True,
    )
    raw_snapshot_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("lead_snapshots.id"),
        nullable=True,
    )
    normalized_json: Mapped[str] = mapped_column(Text, nullable=False)
    rule_score_json: Mapped[str] = mapped_column(Text, nullable=False)
    enrichment_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    review_status: Mapped[str] = mapped_column(String, nullable=False)
    processed_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class ReviewDecisionORM(Base):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("lead_analyses.id"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[str] = mapped_column(String, nullable=False)


Index("idx_lead_analyses_copper_lead_id", LeadAnalysisORM.copper_lead_id)
Index("idx_lead_analyses_batch_run_id", LeadAnalysisORM.batch_run_id)
Index("idx_review_decisions_analysis_id", ReviewDecisionORM.analysis_id)


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_id() -> str:
    return str(uuid.uuid4())


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def deserialize_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def loads_json(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


def build_sqlite_url(db_path: Path | str) -> str:
    path = Path(db_path)
    return f"sqlite:///{path}"


def get_default_database_url() -> str:
    settings = get_settings()
    return settings.database_url


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_default_database_url()

    # For local SQLite files, create the parent directory before SQLAlchemy
    # opens the database so app startup does not fail on a missing folder.
    if url.startswith("sqlite:///") and url != "sqlite:///:memory:":
        sqlite_path = Path(url.removeprefix("sqlite:///"))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    return create_engine(url, future=True)


def create_session_factory(
    database_url: str | None = None,
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    resolved_engine = engine or create_database_engine(database_url)
    return sessionmaker(bind=resolved_engine, expire_on_commit=False, class_=Session)


def initialize_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def lead_analysis_to_stored_record(
    analysis_id: str,
    lead_analysis: LeadAnalysisRecord,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_prompt_version: str | None = None,
) -> StoredLeadAnalysis:
    return StoredLeadAnalysis(
        analysis_id=analysis_id,
        copper_lead_id=lead_analysis.copper_lead_id,
        batch_run_id=lead_analysis.batch_run_id,
        raw_snapshot_id=lead_analysis.raw_snapshot_id,
        normalized_lead=lead_analysis.normalized_lead,
        rule_score=lead_analysis.rule_score,
        enrichment_result=lead_analysis.enrichment_result,
        llm_analysis=lead_analysis.llm_analysis,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_prompt_version=llm_prompt_version,
        review_status=lead_analysis.review_status,
        processed_at=lead_analysis.processed_at,
        updated_at=lead_analysis.updated_at,
    )


def batch_run_orm_to_model(row: BatchRunORM) -> BatchRun:
    return BatchRun(
        run_id=row.id,
        run_type=row.run_type,  # type: ignore[arg-type]
        status=row.status,  # type: ignore[arg-type]
        total_leads=row.total_leads,
        processed_count=row.processed_count,
        success_count=row.success_count,
        failure_count=row.failure_count,
        started_at=deserialize_datetime(row.started_at) or utc_now(),
        completed_at=deserialize_datetime(row.completed_at),
        created_at=deserialize_datetime(row.created_at) or utc_now(),
        updated_at=deserialize_datetime(row.updated_at) or utc_now(),
    )


def lead_snapshot_orm_to_model(row: LeadSnapshotORM) -> LeadSnapshotRecord:
    return LeadSnapshotRecord(
        snapshot_id=row.id,
        copper_lead_id=row.copper_lead_id,
        raw_payload=loads_json(row.raw_payload_json) or {},
        fetched_at=deserialize_datetime(row.fetched_at) or utc_now(),
    )


def lead_analysis_orm_to_model(row: LeadAnalysisORM) -> StoredLeadAnalysis:
    enrichment_json = loads_json(row.enrichment_json)
    llm_output_json = loads_json(row.llm_output_json)

    return StoredLeadAnalysis(
        analysis_id=row.id,
        copper_lead_id=row.copper_lead_id,
        batch_run_id=row.batch_run_id,
        raw_snapshot_id=row.raw_snapshot_id,
        normalized_lead=NormalizedLead.model_validate(loads_json(row.normalized_json)),
        rule_score=RuleScoreResult.model_validate(loads_json(row.rule_score_json)),
        enrichment_result=EnrichmentResult.model_validate(enrichment_json)
        if enrichment_json is not None
        else None,
        llm_analysis=LLMAnalysisResult.model_validate(llm_output_json)
        if llm_output_json is not None
        else None,
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        llm_prompt_version=row.llm_prompt_version,
        review_status=row.review_status,  # type: ignore[arg-type]
        processed_at=deserialize_datetime(row.processed_at) or utc_now(),
        updated_at=deserialize_datetime(row.updated_at) or utc_now(),
    )


def review_decision_orm_to_model(row: ReviewDecisionORM) -> ReviewDecision:
    return ReviewDecision(
        review_id=row.id,
        analysis_id=row.analysis_id,
        decision=row.decision,  # type: ignore[arg-type]
        notes=row.notes,
        decided_at=deserialize_datetime(row.decided_at) or utc_now(),
    )
