

from enum import Enum


class EnquiryStatus(str, Enum):
    """Lifecycle states for an enquiry."""
    PENDING = "pending"         
    PROCESSING = "processing"     
    RESOLVED = "resolved"         
    ESCALATED = "escalated"      


class FollowUpStatus(str, Enum):
    """States for a scheduled follow-up."""
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    """Types of events recorded in conversation_history."""
    ENQUIRY_CREATED = "enquiry_created"
    TASK_STARTED = "task_started"
    SOP_MATCHED = "sop_matched"
    ESCALATION_TRIGGERED = "escalation_triggered"
    FOLLOWUP_CREATED = "followup_created"
    FOLLOWUP_SENT = "followup_sent"
    MANUAL_ESCALATION = "manual_escalation"
    API_ERROR = "api_error"


class Channel(str, Enum):
    """Supported inbound channels."""
    EMAIL = "email"
    CHAT = "chat"
    PHONE = "phone"
    WEB = "web"