

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import EnquiryStatus, EventType
from app.db.models import ConversationHistory, Enquiry
from app.schemas.enquiry_schema import EnquiryCreateRequest
from app.utils.exceptions import EnquiryNotFoundError


def create_enquiry(db: Session, payload: EnquiryCreateRequest) -> Enquiry:
    """
    Persist a new enquiry row and record an ENQUIRY_CREATED history event.

    Args:
        db      : Active SQLAlchemy session.
        payload : Validated request body.

    Returns:
        The newly created Enquiry ORM instance.
    """
    enquiry = Enquiry(
        customer_name=payload.customer_name,
        channel=payload.channel.value,
        message=payload.message,
        status=EnquiryStatus.PENDING.value,
    )
    db.add(enquiry)
    db.flush()  # Get the auto-generated ID before committing

    # Record the creation event in the timeline
    _add_history_event(
        db=db,
        enquiry_id=enquiry.id,
        event_type=EventType.ENQUIRY_CREATED.value,
        message=f"Enquiry received from {payload.customer_name} via {payload.channel.value}.",
    )

    db.commit()
    db.refresh(enquiry)
    return enquiry


def get_enquiry(db: Session, enquiry_id: int) -> Enquiry:
    """
    Fetch a single enquiry by primary key.

    Raises:
        EnquiryNotFoundError: if no row exists with that ID.
    """
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise EnquiryNotFoundError(enquiry_id)
    return enquiry


def get_history(db: Session, enquiry_id: int) -> Enquiry:
    """
    Fetch enquiry with its full timeline and follow-ups eagerly loaded.
    Used by GET /enquiry/{id}/history.

    Raises:
        EnquiryNotFoundError: if enquiry does not exist.
    """
    enquiry = (
        db.query(Enquiry)
        .filter(Enquiry.id == enquiry_id)
        .first()
    )
    if not enquiry:
        raise EnquiryNotFoundError(enquiry_id)

    # Access relationships to trigger loading before session closes
    _ = enquiry.history
    _ = enquiry.followups

    return enquiry


def update_status(
    db: Session,
    enquiry: Enquiry,
    new_status: EnquiryStatus,
    matched_sop: Optional[str] = None,
    suggested_response: Optional[str] = None,
) -> Enquiry:
    """
    Transition enquiry to a new status and optionally set SOP fields.

    Args:
        db                 : Active session.
        enquiry            : ORM instance to update.
        new_status         : Target EnquiryStatus value.
        matched_sop        : SOP name if matched (optional).
        suggested_response : AI-suggested reply text (optional).

    Returns:
        Updated Enquiry instance.
    """
    enquiry.status = new_status.value
    enquiry.updated_at = datetime.utcnow()

    if matched_sop is not None:
        enquiry.matched_sop = matched_sop

    if suggested_response is not None:
        enquiry.suggested_response = suggested_response

    db.commit()
    db.refresh(enquiry)
    return enquiry


def _add_history_event(
    db: Session,
    enquiry_id: int,
    event_type: str,
    message: Optional[str] = None,
) -> ConversationHistory:
    """
    Internal helper — append a single event to conversation_history.
    Does NOT commit; caller is responsible for committing the transaction.
    """
    event = ConversationHistory(
        enquiry_id=enquiry_id,
        event_type=event_type,
        message=message,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    return event


def add_history_event(
    db: Session,
    enquiry_id: int,
    event_type: str,
    message: Optional[str] = None,
) -> ConversationHistory:
    """
    Public wrapper — append a history event and commit immediately.
    Used by services that need to record events outside the creation flow.
    """
    event = _add_history_event(db, enquiry_id, event_type, message)
    db.commit()
    db.refresh(event)
    return event