from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class UploadAnalysis(Base):
    __tablename__ = "upload_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, processing, complete, failed
    file_count = Column(Integer, default=0)
    languages = Column(JSON, default=list)
    frameworks = Column(JSON, default=list)
    architecture_type = Column(String(100), nullable=True)
    architecture_summary = Column(Text, nullable=True)
    folder_tree = Column(JSON, default=list)
    dependencies = Column(JSON, default=dict)
    issues = Column(JSON, default=list)
    security_issues = Column(JSON, default=list)
    performance_issues = Column(JSON, default=list)
    health_score = Column(Float, default=0.0)
    architecture_score = Column(Float, default=0.0)
    debt_score = Column(Float, default=0.0)
    stability_score = Column(Float, default=0.0)
    recommendations = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="upload_analyses")
    project = relationship("Project", back_populates="upload_analyses")
