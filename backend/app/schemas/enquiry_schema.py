

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import Channel, EnquiryStatus, FollowUpStatus


# REQUEST SCHEMAS


class EnquiryCreateRequest(BaseModel):
    """Payload for POST /enquiry"""

    channel: Channel = Field(
        ...,
        description="Inbound channel the customer used.",
        examples=["chat"],
    )
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Full name of the customer.",
        examples=["Alice Johnson"],
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The customer's enquiry message.",
        examples=["Hi, I'd like to make a booking for next Friday."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "channel": "chat",
                "customer_name": "Alice Johnson",
                "message": "Hi, I'd like to make a booking for next Friday.",
            }
        }
    }


class FollowUpCreateRequest(BaseModel):
    """Payload for POST /enquiry/{id}/follow-up"""

    delay_minutes: int = Field(
        ...,
        gt=0,
        description="How many minutes from now the follow-up should be sent.",
        examples=[30],
    )
    message_template: Optional[str] = Field(
        default=None,
        description="Optional custom message. Defaults to a generic follow-up if omitted.",
        examples=["Just checking in — did we resolve your query?"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "delay_minutes": 30,
                "message_template": "Just checking in — did we resolve your query?",
            }
        }
    }


class EscalateRequest(BaseModel):
    """Payload for POST /enquiry/{id}/escalate"""

    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for manual escalation to a human agent.",
        examples=["Customer is very upset and requesting a manager."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reason": "Customer is very upset and requesting a manager.",
            }
        }
    }



# RESPONSE SCHEMAS


class EnquiryCreatedResponse(BaseModel):
    """Returned immediately after POST /enquiry — before background processing."""

    enquiry_id: int = Field(..., description="Unique ID of the created enquiry.")
    status: EnquiryStatus = Field(..., description="Initial status (always 'pending').")
    message: str = Field(..., description="Confirmation message.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "enquiry_id": 1,
                "status": "pending",
                "message": "Enquiry received. Processing started in background.",
            }
        }
    }


class ConversationHistoryItem(BaseModel):
    """A single event in the enquiry timeline."""

    id: int
    event_type: str
    message: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}


class FollowUpItem(BaseModel):
    """A single follow-up record."""

    id: int
    delay_minutes: int
    message_template: Optional[str]
    scheduled_time: datetime
    status: FollowUpStatus

    model_config = {"from_attributes": True}


class EnquiryHistoryResponse(BaseModel):
    """Full detail view returned by GET /enquiry/{id}/history"""

    id: int
    customer_name: str
    channel: str
    message: str
    status: EnquiryStatus
    matched_sop: Optional[str]
    suggested_response: Optional[str]
    created_at: datetime
    updated_at: datetime
    timeline: list[ConversationHistoryItem]
    followups: list[FollowUpItem]

    model_config = {"from_attributes": True}


class FollowUpCreatedResponse(BaseModel):
    """Returned after POST /enquiry/{id}/follow-up"""

    followup_id: int
    enquiry_id: int
    scheduled_time: datetime
    status: FollowUpStatus

    model_config = {"from_attributes": True}


class EscalationResponse(BaseModel):
    """Returned after POST /enquiry/{id}/escalate"""

    enquiry_id: int
    status: EnquiryStatus
    message: str

    model_config = {"from_attributes": True}