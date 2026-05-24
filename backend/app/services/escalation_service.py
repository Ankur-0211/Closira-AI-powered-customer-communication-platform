

from sqlalchemy.orm import Session

from app.core.constants import EnquiryStatus, EventType
from app.db.models import Enquiry
from app.services.enquiry_service import add_history_event, update_status


def auto_escalate(db: Session, enquiry: Enquiry) -> Enquiry:
    """
    Automatically escalate an enquiry when the SOP matcher finds no match.

    Records an ESCALATION_TRIGGERED history event and transitions
    the enquiry status to ESCALATED.

    Args:
        db      : Active SQLAlchemy session.
        enquiry : The enquiry ORM instance to escalate.

    Returns:
        Updated Enquiry instance.
    """
    # Record the auto-escalation event in the timeline
    add_history_event(
        db=db,
        enquiry_id=enquiry.id,
        event_type=EventType.ESCALATION_TRIGGERED.value,
        message=(
            "No SOP match found for this enquiry. "
            "Automatically escalated to a human agent for review."
        ),
    )

    # Transition status
    updated = update_status(
        db=db,
        enquiry=enquiry,
        new_status=EnquiryStatus.ESCALATED,
    )

    return updated


def manual_escalate(db: Session, enquiry: Enquiry, reason: str) -> Enquiry:
    """
    Manually escalate an enquiry via the API endpoint.

    Records a MANUAL_ESCALATION history event with the provided reason
    and transitions the enquiry status to ESCALATED.

    Args:
        db      : Active SQLAlchemy session.
        enquiry : The enquiry ORM instance to escalate.
        reason  : Human-provided reason for escalation.

    Returns:
        Updated Enquiry instance.
    """
    add_history_event(
        db=db,
        enquiry_id=enquiry.id,
        event_type=EventType.MANUAL_ESCALATION.value,
        message=f"Manual escalation requested. Reason: {reason}",
    )

    updated = update_status(
        db=db,
        enquiry=enquiry,
        new_status=EnquiryStatus.ESCALATED,
    )

    return updated