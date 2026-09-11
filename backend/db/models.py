from sqlalchemy import Column, String, DateTime, JSON, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    upload_quota = Column(Integer, default=5, nullable=False)
    uploads_used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(String, index=True, nullable=True)
    filename = Column(String, nullable=False)
    status = Column(String, default=DocumentStatus.PENDING.value, index=True)
    
    extracted_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="documents")
