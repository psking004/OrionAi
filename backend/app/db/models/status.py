from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectStatus(Base):
    __tablename__ = "project_statuses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    progress = Column(String(50), nullable=False, default="unknown")
    problems = Column(Text, nullable=True)          # JSON list stored as text
    stuck_points = Column(Text, nullable=True)      # JSON list stored as text
    next_steps = Column(Text, nullable=True)        # JSON list stored as text
    missing_features = Column(Text, nullable=True)  # JSON list stored as text
    health_score = Column(Float, nullable=False, default=50.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="statuses")

    __table_args__ = (
        Index("ix_project_statuses_project_created", "project_id", "created_at"),
    )
