

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import EventType
from app.db.database import check_db_connection, get_db
from app.schemas.enquiry_schema import (
    EnquiryCreateRequest,
    EnquiryCreatedResponse,
    EnquiryHistoryResponse,
    EscalateRequest,
    EscalationResponse,
    FollowUpCreatedResponse,
    FollowUpCreateRequest,
)
from app.schemas.response_schema import APIResponse, HealthResponse
from app.services.enquiry_service import (
    create_enquiry,
    get_enquiry,
    get_history,
)
from app.services.escalation_service import manual_escalate
from app.services.followup_service import schedule_followup
from app.utils.exceptions import EnquiryNotFoundError
from app.workers.background_tasks import process_enquiry

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# POST /enquiry
# ---------------------------------------------------------------------------

@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=APIResponse[EnquiryCreatedResponse],
    summary="Create a new customer enquiry",
    description=(
        "Accepts an inbound customer enquiry, persists it immediately, "
        "and triggers asynchronous SOP matching in the background. "
        "Returns the enquiry ID right away — no need to wait for processing."
    ),
)
def create_enquiry_endpoint(
    payload: EnquiryCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    enquiry = create_enquiry(db=db, payload=payload)

    # Kick off background processing — response is returned before this finishes
    background_tasks.add_task(process_enquiry, enquiry.id)

    logger.info(
        "Enquiry created.",
        extra={
            "event_type": EventType.ENQUIRY_CREATED.value,
            "enquiry_id": enquiry.id,
            "customer": payload.customer_name,
            "channel": payload.channel.value,
        },
    )

    return APIResponse(
        success=True,
        message="Enquiry received. Processing started in background.",
        data=EnquiryCreatedResponse(
            enquiry_id=enquiry.id,
            status=enquiry.status,
            message="Enquiry received. Processing started in background.",
        ),
    )


# ---------------------------------------------------------------------------
# POST /enquiry/{id}/follow-up
# ---------------------------------------------------------------------------

@router.post(
    "/{enquiry_id}/follow-up",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse[FollowUpCreatedResponse],
    summary="Schedule a follow-up for an enquiry",
    description=(
        "Schedules a follow-up message to be sent after a specified delay. "
        "An optional custom message template can be provided; "
        "a generic default is used if omitted."
    ),
)
def schedule_followup_endpoint(
    enquiry_id: int,
    payload: FollowUpCreateRequest,
    db: Session = Depends(get_db),
):
    # Verify enquiry exists — raises 404 if not
    get_enquiry(db=db, enquiry_id=enquiry_id)

    followup = schedule_followup(
        db=db,
        enquiry_id=enquiry_id,
        delay_minutes=payload.delay_minutes,
        message_template=payload.message_template,
    )

    logger.info(
        "Follow-up scheduled.",
        extra={
            "event_type": EventType.FOLLOWUP_CREATED.value,
            "enquiry_id": enquiry_id,
            "followup_id": followup.id,
            "delay_minutes": payload.delay_minutes,
        },
    )

    return APIResponse(
        success=True,
        message=f"Follow-up scheduled in {payload.delay_minutes} minute(s).",
        data=FollowUpCreatedResponse(
            followup_id=followup.id,
            enquiry_id=enquiry_id,
            scheduled_time=followup.scheduled_time,
            status=followup.status,
        ),
    )


# ---------------------------------------------------------------------------
# POST /enquiry/{id}/escalate
# ---------------------------------------------------------------------------

@router.post(
    "/{enquiry_id}/escalate",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse[EscalationResponse],
    summary="Manually escalate an enquiry to a human agent",
    description=(
        "Transitions the enquiry to ESCALATED status and records "
        "the escalation reason in the conversation timeline."
    ),
)
def escalate_enquiry_endpoint(
    enquiry_id: int,
    payload: EscalateRequest,
    db: Session = Depends(get_db),
):
    enquiry = get_enquiry(db=db, enquiry_id=enquiry_id)

    updated = manual_escalate(db=db, enquiry=enquiry, reason=payload.reason)

    logger.warning(
        "Manual escalation triggered.",
        extra={
            "event_type": EventType.MANUAL_ESCALATION.value,
            "enquiry_id": enquiry_id,
            "reason": payload.reason,
        },
    )

    return APIResponse(
        success=True,
        message="Enquiry has been escalated to a human agent.",
        data=EscalationResponse(
            enquiry_id=updated.id,
            status=updated.status,
            message="Enquiry has been escalated to a human agent.",
        ),
    )


# ---------------------------------------------------------------------------
# GET /enquiry/{id}/history
# ---------------------------------------------------------------------------

@router.get(
    "/{enquiry_id}/history",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse[EnquiryHistoryResponse],
    summary="Retrieve full enquiry history and timeline",
    description=(
        "Returns the complete enquiry record including: "
        "enquiry details, conversation timeline, scheduled follow-ups, "
        "SOP match result, and escalation history."
    ),
)
def get_enquiry_history_endpoint(
    enquiry_id: int,
    db: Session = Depends(get_db),
):
    enquiry = get_history(db=db, enquiry_id=enquiry_id)

    return APIResponse(
        success=True,
        message="Enquiry history retrieved successfully.",
        data=EnquiryHistoryResponse(
            id=enquiry.id,
            customer_name=enquiry.customer_name,
            channel=enquiry.channel,
            message=enquiry.message,
            status=enquiry.status,
            matched_sop=enquiry.matched_sop,
            suggested_response=enquiry.suggested_response,
            created_at=enquiry.created_at,
            updated_at=enquiry.updated_at,
            timeline=[
                {
                    "id": h.id,
                    "event_type": h.event_type,
                    "message": h.message,
                    "timestamp": h.timestamp,
                }
                for h in enquiry.history
            ],
            followups=[
                {
                    "id": f.id,
                    "delay_minutes": f.delay_minutes,
                    "message_template": f.message_template,
                    "scheduled_time": f.scheduled_time,
                    "status": f.status,
                }
                for f in enquiry.followups
            ],
        ),
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse[HealthResponse],
    summary="API and database health check",
    description="Returns the current health status of the API and database connectivity.",
    tags=["Health"],
)
def health_check():
    db_status = "connected" if check_db_connection() else "unreachable"

    return APIResponse(
        success=True,
        message="Service is healthy." if db_status == "connected" else "Database unreachable.",
        data=HealthResponse(
            status="healthy" if db_status == "connected" else "degraded",
            database=db_status,
            version=settings.APP_VERSION,
        ),
    )

