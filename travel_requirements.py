from __future__ import annotations

import re
from dataclasses import dataclass

from attraction_availability import extract_requested_dates


BROAD_DESTINATIONS = (
    "india",
    "arunachal pradesh",
    "arunanchal pradesh",
    "himachal pradesh",
    "uttarakhand",
    "rajasthan",
    "kerala",
    "goa",
    "karnataka",
    "maharashtra",
    "delhi",
    "assam",
    "sikkim",
    "meghalaya",
)


@dataclass(frozen=True)
class RequirementCheck:
    is_complete: bool
    message: str


def check_hotel_pricing_requirements(user_query: str) -> RequirementCheck:
    missing = []
    query = user_query.lower()

    if not has_origin(query):
        missing.append("starting city/source location, for example from Delhi, Mumbai, Kolkata")

    if not has_hotel_dates(user_query):
        missing.append("journey start date and trip duration, or hotel check-in/check-out dates")

    if not has_guest_count(query):
        missing.append("number of travellers/guests")

    if missing:
        questions = "\n".join(f"- {item}" for item in missing)
        return RequirementCheck(
            is_complete=False,
            message=(
                "To show exact hotel names, booking links, and source-listed prices, "
                "I need a few details first:\n"
                f"{questions}\n\n"
                "Example: Plan 7 days in Arunachal Pradesh from Delhi under 30000, "
                "starting 24 August 2026, 2 travellers. You do not need to know the internal places."
            ),
        )

    return RequirementCheck(is_complete=True, message="")


def has_hotel_dates(user_query: str) -> bool:
    dates = extract_requested_dates(user_query)
    has_two_dates = len(dates) >= 2
    has_start_plus_duration = bool(dates) and bool(
        re.search(r"\b\d+\s*(?:day|days|night|nights)\b", user_query, re.IGNORECASE)
    )

    return has_two_dates or has_start_plus_duration


def has_guest_count(query: str) -> bool:
    if re.search(r"\b(?:solo|alone)\b", query):
        return True

    if re.search(r"\b(?:couple|honeymoon)\b", query):
        return True

    return bool(
        re.search(
            r"\b\d+\s*(?:travellers|travelers|people|persons|adults|guests|members)\b",
            query,
        )
    )


def has_origin(query: str) -> bool:
    return bool(
        re.search(
            r"\b(?:from|starting from|departing from|coming from|i live in)\s+[a-z][a-z\s]+",
            query,
        )
    )


def has_specific_destination(query: str) -> bool:
    for broad_destination in BROAD_DESTINATIONS:
        if broad_destination in query:
            return has_city_hint(query, broad_destination)

    return True


def has_city_hint(query: str, broad_destination: str) -> bool:
    destination_patterns = (
        rf"\b(?:in|to|visit)\s+[a-z][a-z\s]+,\s*{re.escape(broad_destination)}\b",
        rf"\b(?:tawang|ziro|bomdila|itanagar|dirang|panaji|jaipur|udaipur|munnar|kochi|manali|shimla|rishikesh|gangtok)\b",
    )

    return any(re.search(pattern, query) for pattern in destination_patterns)
