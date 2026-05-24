
from dataclasses import dataclass
from typing import Optional


@dataclass
class SOPMatch:
    """Result returned when a message matches an SOP category."""
    name: str
    suggested_response: str


# SOP DEFINITIONS
# Each SOP has a name, a list of trigger keywords, and a suggested response.

SOP_DEFINITIONS: list[dict] = [
    {
        "name": "Booking Enquiry",
        "keywords": ["booking", "reserve", "appointment", "schedule", "book"],
        "suggested_response": (
            "Thank you for reaching out! We'd be happy to help you with your booking. "
            "Please share your preferred date and time, and we'll confirm availability right away."
        ),
    },
    {
        "name": "Pricing Question",
        "keywords": ["price", "pricing", "quote", "cost", "charge", "fee", "rate"],
        "suggested_response": (
            "Great question! Our pricing varies depending on the service selected. "
            "Could you share more details about what you're looking for so we can "
            "provide an accurate quote?"
        ),
    },
    {
        "name": "Complaint",
        "keywords": ["issue", "complaint", "unhappy", "bad service", "disappointed",
                     "problem", "terrible", "awful", "unacceptable"],
        "suggested_response": (
            "We're truly sorry to hear about your experience. "
            "Your feedback is very important to us. "
            "A senior team member will review your case and reach out to you shortly."
        ),
    },
    {
        "name": "After Hours",
        "keywords": ["closed", "late", "unavailable", "after hours", "weekend",
                     "holiday", "not available"],
        "suggested_response": (
            "Thank you for contacting us! Our team is currently outside business hours. "
            "We'll get back to you as soon as we're back. "
            "Our operating hours are Monday–Friday, 9 AM – 6 PM."
        ),
    },
    {
        "name": "Support Request",
        "keywords": ["help", "support", "problem", "assist", "assistance",
                     "not working", "error", "fix", "trouble"],
        "suggested_response": (
            "We're here to help! Could you describe the issue you're experiencing in "
            "a bit more detail? Our support team will look into it and get back to you promptly."
        ),
    },
]


def match_sop(message: str) -> Optional[SOPMatch]:
    """
    Scan the customer message against all SOP keyword lists.

    Matching strategy:
    - Normalise message to lowercase
    - For each SOP, count how many of its keywords appear in the message
    - Return the SOP with the highest keyword hit count
    - Return None if no keywords match at all

    Args:
        message: Raw customer enquiry text.

    Returns:
        SOPMatch with name + suggested_response, or None.
    """
    normalised = message.lower()

    best_match: Optional[dict] = None
    best_score: int = 0

    for sop in SOP_DEFINITIONS:
        score = sum(1 for keyword in sop["keywords"] if keyword in normalised)
        if score > best_score:
            best_score = score
            best_match = sop

    if best_match is None or best_score == 0:
        return None

    return SOPMatch(
        name=best_match["name"],
        suggested_response=best_match["suggested_response"],
    )