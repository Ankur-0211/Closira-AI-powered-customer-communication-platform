


class EnquiryNotFoundError(Exception):
    """Raised when an enquiry ID does not exist in the database."""

    def __init__(self, enquiry_id: int):
        self.enquiry_id = enquiry_id
        super().__init__(f"Enquiry with id={enquiry_id} does not exist.")


class DatabaseError(Exception):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, detail: str = "A database error occurred."):
        super().__init__(detail)


class SOPMatchError(Exception):
    """Raised when the SOP matching engine encounters an unexpected error."""

    def __init__(self, detail: str = "SOP matching failed."):
        super().__init__(detail)


class FollowUpNotFoundError(Exception):
    """Raised when a follow-up ID does not exist in the database."""

    def __init__(self, followup_id: int):
        self.followup_id = followup_id
        super().__init__(f"Follow-up with id={followup_id} does not exist.")


class InvalidStatusTransitionError(Exception):
    """
    Raised when an enquiry cannot be transitioned to the requested status.
    Example: trying to escalate an already-resolved enquiry.
    """

    def __init__(self, current: str, target: str):
        super().__init__(
            f"Cannot transition enquiry from '{current}' to '{target}'."
        )