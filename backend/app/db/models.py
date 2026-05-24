

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Enquiry(Base):
    """
    Core table — one row per inbound customer enquiry.
    Status progresses: pending → processing → resolved | escalated
    """
    __tablename__ = "enquiries"

    id                 = Column(Integer, primary_key=True, index=True)
    customer_name      = Column(String(120), nullable=False)
    channel            = Column(String(50), nullable=False)        
    message            = Column(Text, nullable=False)
    status             = Column(String(50), nullable=False, default="pending")
    matched_sop        = Column(String(120), nullable=True)          
    suggested_response = Column(Text, nullable=True)                
    created_at         = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at         = Column(DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow, nullable=False)

  
    history   = relationship("ConversationHistory", back_populates="enquiry",
                             cascade="all, delete-orphan", order_by="ConversationHistory.timestamp")
    followups = relationship("FollowUp", back_populates="enquiry",
                             cascade="all, delete-orphan", order_by="FollowUp.scheduled_time")

    def __repr__(self) -> str:
        return f"<Enquiry id={self.id} customer={self.customer_name} status={self.status}>"


class ConversationHistory(Base):
    """
    Append-only event log for an enquiry.
    Every significant action (created, matched, escalated, follow-up sent)
    is recorded here to build a complete timeline.
    """
    __tablename__ = "conversation_history"

    id          = Column(Integer, primary_key=True, index=True)
    enquiry_id  = Column(Integer, ForeignKey("enquiries.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    event_type  = Column(String(80), nullable=False)   # maps to EventType enum
    message     = Column(Text, nullable=True)          # human-readable event description
    timestamp   = Column(DateTime, default=datetime.utcnow, nullable=False)

    enquiry = relationship("Enquiry", back_populates="history")

    def __repr__(self) -> str:
        return f"<ConversationHistory id={self.id} enquiry_id={self.enquiry_id} event={self.event_type}>"


class FollowUp(Base):
    """
    Scheduled follow-up messages for an enquiry.
    Status: scheduled → sent | cancelled
    """
    __tablename__ = "followups"

    id               = Column(Integer, primary_key=True, index=True)
    enquiry_id       = Column(Integer, ForeignKey("enquiries.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    delay_minutes    = Column(Integer, nullable=False)
    message_template = Column(Text, nullable=True)     # optional custom message
    scheduled_time   = Column(DateTime, nullable=False)
    status           = Column(String(50), nullable=False, default="scheduled")
    created_at       = Column(DateTime, default=datetime.utcnow, nullable=False)

    enquiry = relationship("Enquiry", back_populates="followups")

    def __repr__(self) -> str:
        return f"<FollowUp id={self.id} enquiry_id={self.enquiry_id} status={self.status}>"