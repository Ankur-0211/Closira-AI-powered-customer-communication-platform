

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import EventType, FollowUpStatus
from app.db.models import FollowUp
from app.services.enquiry_service import add_history_event


def schedule_followup(
    db: Session,
    enquiry_id: int,
    delay_minutes: int,
    message_template: Optional[str] = None,
) -> FollowUp:
    """
    Create a new follow-up record scheduled `delay_minutes` from now.

    Also appends a FOLLOWUP_CREATED event to the enquiry timeline.

    Args:
        db               : Active SQLAlchemy session.
        enquiry_id       : ID of the parent enquiry.
        delay_minutes    : Minutes from now when the follow-up is due.
        message_template : Optional custom message; defaults to generic text.

    Returns:
        The newly created FollowUp ORM instance.
    """
    scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)

    # Use a sensible default if no custom template provided
    resolved_template = message_template or (
        "Hi, we just wanted to follow up on your recent enquiry. "
        "Please let us know if you need any further assistance."
    )

    followup = FollowUp(
        enquiry_id=enquiry_id,
        delay_minutes=delay_minutes,
        message_template=resolved_template,
        scheduled_time=scheduled_time,
        status=FollowUpStatus.SCHEDULED.value,
    )
    db.add(followup)
    db.flush()  # Obtain ID before commit

    # Record the event in the timeline
    add_history_event(
        db=db,
        enquiry_id=enquiry_id,
        event_type=EventType.FOLLOWUP_CREATED.value,
        message=(
            f"Follow-up scheduled in {delay_minutes} minute(s) "
            f"(due at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)."
        ),
    )

    db.commit()
    db.refresh(followup)
    return followup


def mark_followup_sent(db: Session, followup: FollowUp) -> FollowUp:
    """
    Transition a follow-up to SENT status.
    Also appends a FOLLOWUP_SENT event to the parent enquiry timeline.

    Args:
        db      : Active SQLAlchemy session.
        followup: The FollowUp ORM instance to update.

    Returns:
        Updated FollowUp instance.
    """
    followup.status = FollowUpStatus.SENT.value
    db.commit()
    db.refresh(followup)

    add_history_event(
        db=db,
        enquiry_id=followup.enquiry_id,
        event_type=EventType.FOLLOWUP_SENT.value,
        message=f"Follow-up (id={followup.id}) marked as sent.",
    )

    return followup


def get_followup(db: Session, followup_id: int) -> Optional[FollowUp]:
    """Fetch a single follow-up by primary key. Returns None if not found."""
    return db.query(FollowUp).filter(FollowUp.id == followup_id).first()