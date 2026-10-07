"""Scan ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Text, Integer
from app.database import Base


class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), nullable=False)
    status = Column(String(30), default="pending")            # pending|running|completed|failed
    progress_step = Column(String(100), nullable=True)
    security_score = Column(Float, nullable=True)
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    scanners_used = Column(Text, nullable=True)               # JSON list
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
