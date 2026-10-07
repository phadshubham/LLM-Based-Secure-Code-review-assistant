"""Project ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)          # "zip" | "github"
    repository_url = Column(Text, nullable=True)
    language = Column(Text, nullable=True)                    # JSON-encoded list
    dependencies = Column(Text, nullable=True)                # JSON-encoded dict
    project_path = Column(Text, nullable=True)                # absolute path on server
    created_at = Column(DateTime, default=datetime.utcnow)
