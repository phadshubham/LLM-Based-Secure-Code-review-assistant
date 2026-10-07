"""AI Review ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class AIReview(Base):
    __tablename__ = "ai_reviews"

    review_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id = Column(String(36), nullable=False)
    explanation = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    suggested_patch = Column(Text, nullable=True)
    confidence = Column(String(20), nullable=True)            # high|medium|low
    classification = Column(String(30), nullable=True)        # VERIFIED_FINDING|AI_OBSERVATION|AI_PATCH
    source = Column(String(50), nullable=True)                # e.g. "qwen2.5-coder:3b"
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
