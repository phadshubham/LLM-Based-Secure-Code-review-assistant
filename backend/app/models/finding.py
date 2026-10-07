"""Finding ORM model."""

import uuid
from sqlalchemy import Column, String, Integer, Text, Boolean
from app.database import Base


class Finding(Base):
    __tablename__ = "findings"

    finding_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String(36), nullable=False)
    tool = Column(String(50), nullable=False)
    rule_id = Column(String(255), nullable=True)
    file = Column(Text, nullable=False)
    line = Column(Integer, nullable=True)
    column = Column(Integer, nullable=True)
    severity = Column(String(20), nullable=False)   # CRITICAL|HIGH|MEDIUM|LOW|INFO
    category = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    verified = Column(Boolean, default=True)        # True = scanner-confirmed
    status = Column(String(20), default="open")     # open|acknowledged|fixed
