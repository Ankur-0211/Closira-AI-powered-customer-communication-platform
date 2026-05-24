

import logging

from sqlalchemy.orm import Session

from app.core.constants import EnquiryStatus, EventType
from app.db.database import SessionLocal
from app.services.enquiry_service import add_history_event, get_enquiry, update_status
from app.services.escalation_service import auto_escalate
from app.services.sop_matcher import match_sop

logger = logging.getLogger(__name__)


def process_enquiry(enquiry_id: int) -> None:
    """
    Background task — processes a newly created enquiry.

    Opens its own DB session (independent of the request session)
    so it can safely run after the HTTP response has been returned.

    Args:
        enquiry_id: Primary key of the enquiry to process.
    """
    db: Session = SessionLocal()

    try:
        logger.info(
            "Background task started.",
            extra={"event_type": EventType.TASK_STARTED.value, "enquiry_id": enquiry_id},
        )

        # ---------------------------------------------------------------
        # Step 1 — Fetch enquiry and move to PROCESSING
        # ---------------------------------------------------------------
        enquiry = get_enquiry(db, enquiry_id)

        update_status(db=db, enquiry=enquiry, new_status=EnquiryStatus.PROCESSING)

        add_history_event(
            db=db,
            enquiry_id=enquiry_id,
            event_type=EventType.TASK_STARTED.value,
            message="Background processing started. Running SOP matching.",
        )

        # ---------------------------------------------------------------
        # Step 2 — Run SOP matcher
        # ---------------------------------------------------------------
        sop_result = match_sop(enquiry.message)

        # ---------------------------------------------------------------
        # Step 3a — SOP matched → resolve enquiry
        # ---------------------------------------------------------------
        if sop_result:
            logger.info(
                "SOP matched.",
                extra={
                    "event_type": EventType.SOP_MATCHED.value,
                    "enquiry_id": enquiry_id,
                    "sop": sop_result.name,
                },
            )

            update_status(
                db=db,
                enquiry=enquiry,
                new_status=EnquiryStatus.RESOLVED,
                matched_sop=sop_result.name,
                suggested_response=sop_result.suggested_response,
            )

            add_history_event(
                db=db,
                enquiry_id=enquiry_id,
                event_type=EventType.SOP_MATCHED.value,
                message=(
                    f"SOP matched: '{sop_result.name}'. "
                    "Suggested response generated and stored."
                ),
            )

        # ---------------------------------------------------------------
        # Step 3b — No SOP match → auto-escalate
        # ---------------------------------------------------------------
        else:
            logger.warning(
                "No SOP match found. Triggering auto-escalation.",
                extra={
                    "event_type": EventType.ESCALATION_TRIGGERED.value,
                    "enquiry_id": enquiry_id,
                },
            )

            auto_escalate(db=db, enquiry=enquiry)

    except Exception as exc:
        logger.error(
            "Background task failed.",
            extra={
                "event_type": EventType.API_ERROR.value,
                "enquiry_id": enquiry_id,
                "error": str(exc),
            },
        )
        # Best-effort: try to record the failure in the timeline
        try:
            add_history_event(
                db=db,
                enquiry_id=enquiry_id,
                event_type=EventType.API_ERROR.value,
                message=f"Background task error: {str(exc)}",
            )
        except Exception:
            pass  # If DB is also broken, silently skip

    finally:
        db.close()