from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from db import Base


class Objective(Base):
    __tablename__ = "objectives"

    id = Column(Integer, primary_key=True, index=True)
    notion_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    team = Column(String(255), nullable=True)
    quarter = Column(String(100), nullable=True)
    status = Column(String(100), nullable=True)
    progress = Column(Float, default=0.0)
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    key_results = relationship("KeyResult", back_populates="objective", cascade="all, delete-orphan")


class KeyResult(Base):
    __tablename__ = "key_results"

    id = Column(Integer, primary_key=True, index=True)
    notion_id = Column(String(100), unique=True, index=True, nullable=False)
    objective_id = Column(Integer, ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    team = Column(String(255), nullable=True)
    risk = Column(String(100), nullable=True)
    status = Column(String(100), nullable=True)
    progress = Column(Float, default=0.0)
    deadline = Column(Date, nullable=True)
    last_update = Column(Date, nullable=True)
    is_blocked = Column(Boolean, default=False)
    blocker_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    objective = relationship("Objective", back_populates="key_results")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    routed_agent = Column(String(100), nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
