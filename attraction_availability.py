from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta


MONTHS = {
    month.lower(): index
    for index, month in enumerate(calendar.month_name)
    if month
}
MONTHS.update(
    {
        month.lower(): index
        for index, month in enumerate(calendar.month_abbr)
        if month
    }
)


@dataclass(frozen=True)
class AttractionRule:
    name: str
    aliases: tuple[str, ...]
    city: str
    country: str
    closed_weekdays: tuple[int, ...]
    normal_hours: str
    source_name: str
    source_url: str
    alternative_places: tuple[str, ...]
    notes: tuple[str, ...] = ()


TRUSTED_ATTRACTION_RULES = (
    AttractionRule(
        name="Taj Mahal",
        aliases=("taj mahal", "tajmahal"),
        city="Agra",
        country="India",
        closed_weekdays=(4,),
        normal_hours="30 minutes before sunrise to 30 minutes before sunset",
        source_name="Official Taj Mahal website, Department of Tourism, Government of Uttar Pradesh",
        source_url="https://www.tajmahal.gov.in/visiting-hours.aspx",
        alternative_places=(
            "Agra Fort",
            "Mehtab Bagh / Taj View Point",
            "Itimad-ud-Daulah",
            "Fatehpur Sikri",
        ),
        notes=(
            "General viewing is closed every Friday.",
            "Night viewing has separate rules and ticketing, and is also closed every Friday.",
        ),
    ),
    AttractionRule(
        name="Fatehpur Sikri",
        aliases=("fatehpur sikri", "fateh pur sikri"),
        city="Agra",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to sunset",
        source_name="Archaeological Survey of India, Agra Circle",
        source_url="https://www.asiagracircle.in/fateh-pur.html",
        alternative_places=(
            "Agra Fort",
            "Akbar's Tomb",
            "Mariam's Tomb",
            "Ram Bagh",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Akbar's Tomb",
        aliases=("akbar's tomb", "akbar tomb", "akbars tomb", "sikandra"),
        city="Agra",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to sunset",
        source_name="Archaeological Survey of India, Agra Circle",
        source_url="https://www.asiagracircle.in/other-tick.html",
        alternative_places=(
            "Mariam's Tomb",
            "Ram Bagh",
            "Agra Fort",
            "Fatehpur Sikri",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Mariam's Tomb",
        aliases=("mariam's tomb", "mariam tomb", "mariams tomb", "marium tomb"),
        city="Agra",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to sunset",
        source_name="Archaeological Survey of India, Agra Circle",
        source_url="https://www.asiagracircle.in/marium-tomb-sikandra.html",
        alternative_places=(
            "Akbar's Tomb",
            "Ram Bagh",
            "Agra Fort",
            "Fatehpur Sikri",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Ram Bagh",
        aliases=("ram bagh", "rambagh", "aram bagh"),
        city="Agra",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to sunset",
        source_name="Archaeological Survey of India, Agra Circle",
        source_url="https://www.asiagracircle.in/ram-bagh-other.html",
        alternative_places=(
            "Mariam's Tomb",
            "Akbar's Tomb",
            "Agra Fort",
            "Fatehpur Sikri",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Qutub Minar",
        aliases=("qutub minar", "qutab minar", "qutb minar"),
        city="Delhi",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to 8:00 PM",
        source_name="Delhi Tourism, Government of NCT of Delhi",
        source_url="https://www.delhitourism.gov.in/tourist_place/qutab_minar.html",
        alternative_places=(
            "Humayun's Tomb",
            "India Gate",
            "National Museum",
            "Lodhi Garden",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Humayun's Tomb",
        aliases=("humayun's tomb", "humayun tomb", "humayuns tomb"),
        city="Delhi",
        country="India",
        closed_weekdays=(),
        normal_hours="Sunrise to 7:30 PM",
        source_name="Delhi Tourism, Government of NCT of Delhi",
        source_url="https://delhitourism.gov.in/dt/explore_the_city/humayuns_tomb.html",
        alternative_places=(
            "Qutub Minar",
            "India Gate",
            "National Museum",
            "Lodhi Garden",
        ),
        notes=("The official page says it is open all days.",),
    ),
    AttractionRule(
        name="Ajanta Caves",
        aliases=("ajanta caves", "ajanta cave", "ajanta"),
        city="Chhatrapati Sambhajinagar",
        country="India",
        closed_weekdays=(0,),
        normal_hours="Open to visitors on all days except Mondays",
        source_name="Department of Tourism, Government of Maharashtra",
        source_url="https://maharashtratourism.gov.in/cave/ajanta/",
        alternative_places=(
            "Bibi Ka Maqbara",
            "Daulatabad Fort",
            "Chhatrapati Sambhajinagar local markets",
            "Panchakki",
        ),
        notes=("The official page says the site is open to visitors on all days except Mondays.",),
    ),
    AttractionRule(
        name="Ellora Caves",
        aliases=("ellora caves", "ellora cave", "ellora"),
        city="Chhatrapati Sambhajinagar",
        country="India",
        closed_weekdays=(),
        normal_hours="9:00 AM to 5:00 PM",
        source_name="Department of Tourism, Government of Maharashtra",
        source_url="https://maharashtratourism.gov.in/tourist-intrests/caves/",
        alternative_places=(
            "Daulatabad Fort",
            "Bibi Ka Maqbara",
            "Ghrishneshwar Temple",
            "Chhatrapati Sambhajinagar local markets",
        ),
        notes=("The official page lists opening hours but no weekly closed day.",),
    ),
    AttractionRule(
        name="Elephanta Caves",
        aliases=("elephanta caves", "elephanta cave", "elephanta"),
        city="Mumbai",
        country="India",
        closed_weekdays=(0,),
        normal_hours="Open daily except Monday",
        source_name="Department of Tourism, Government of Maharashtra",
        source_url="https://maharashtratourism.gov.in/mr/cave/elephanta/",
        alternative_places=(
            "Gateway of India",
            "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya",
            "Marine Drive",
            "Kala Ghoda",
        ),
        notes=("The official Maharashtra Tourism page says it is open daily except Monday.",),
    ),
)


def find_mentioned_attractions(user_query: str) -> list[AttractionRule]:
    query = user_query.lower()
    matches = []

    for rule in TRUSTED_ATTRACTION_RULES:
        if any(alias in query for alias in rule.aliases):
            matches.append(rule)

    return matches


def extract_requested_dates(user_query: str, default_year: int | None = None) -> list[date]:
    default_year = default_year or date.today().year
    found_dates: list[date] = []

    for match in re.finditer(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", user_query):
        year, month, day = (int(part) for part in match.groups())
        _append_valid_date(found_dates, year, month, day)

    month_names = "|".join(re.escape(name) for name in sorted(MONTHS, key=len, reverse=True))
    day_month_pattern = re.compile(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({month_names})(?:\s+(20\d{{2}}))?\b",
        re.IGNORECASE,
    )

    for match in day_month_pattern.finditer(user_query):
        day_text, month_text, year_text = match.groups()
        year = int(year_text) if year_text else default_year
        month = MONTHS[month_text.lower()]
        day = int(day_text)
        _append_valid_date(found_dates, year, month, day)

    return _dedupe_dates(found_dates)


def check_attraction_availability(user_query: str) -> str:
    attractions = find_mentioned_attractions(user_query)
    requested_dates = extract_requested_dates(user_query)

    if not attractions:
        return (
            "No trusted attraction-specific closure rule matched the query. "
            "The itinerary should avoid making closure claims unless an official source is available."
        )

    if not requested_dates:
        return _format_no_date_result(attractions)

    sections = []
    for attraction in attractions:
        sections.append(_format_attraction_result(attraction, requested_dates))

    return "\n\n".join(sections)


def _format_no_date_result(attractions: list[AttractionRule]) -> str:
    lines = [
        "Trusted attraction availability check:",
        "No exact visit date was detected, so only standing official rules are available.",
    ]

    for attraction in attractions:
        closed_days = ", ".join(calendar.day_name[day] for day in attraction.closed_weekdays)
        closed_rule = (
            f"closed on {closed_days}"
            if closed_days
            else "no weekly closed day listed by this official source"
        )
        lines.extend(
            [
                "",
                f"- {attraction.name} ({attraction.city}, {attraction.country})",
                f"  Official rule: {closed_rule}.",
                f"  Normal hours: {attraction.normal_hours}.",
                f"  Source: {attraction.source_name} - {attraction.source_url}",
            ]
        )

    return "\n".join(lines)


def _format_attraction_result(attraction: AttractionRule, requested_dates: list[date]) -> str:
    lines = [
        f"Trusted availability check for {attraction.name} ({attraction.city}, {attraction.country}):",
        f"Source: {attraction.source_name} - {attraction.source_url}",
        f"Normal hours: {attraction.normal_hours}.",
    ]

    for visit_date in requested_dates:
        weekday_name = calendar.day_name[visit_date.weekday()]

        if visit_date.weekday() in attraction.closed_weekdays:
            suggested_date = _next_open_date(visit_date, attraction)
            alternatives = ", ".join(attraction.alternative_places)
            lines.extend(
                [
                    "",
                    f"- {visit_date.isoformat()} ({weekday_name}): CLOSED.",
                    f"  Reason: official weekly closure for {attraction.name}.",
                    f"  Itinerary action: move {attraction.name} to {suggested_date.isoformat()} "
                    f"({calendar.day_name[suggested_date.weekday()]}).",
                    f"  Use the closed day for: {alternatives}.",
                ]
            )
        else:
            official_rule_note = (
                "under the standing official rule"
                if attraction.closed_weekdays
                else "because the official source does not list this date as a weekly closure"
            )
            lines.extend(
                [
                    "",
                    f"- {visit_date.isoformat()} ({weekday_name}): OPEN {official_rule_note}.",
                    "  Itinerary action: this attraction may be scheduled on this date.",
                ]
            )

    if attraction.notes:
        lines.append("")
        lines.extend(f"Note: {note}" for note in attraction.notes)

    return "\n".join(lines)


def _next_open_date(start_date: date, attraction: AttractionRule) -> date:
    candidate = start_date + timedelta(days=1)

    for _ in range(14):
        if candidate.weekday() not in attraction.closed_weekdays:
            return candidate
        candidate += timedelta(days=1)

    return start_date


def _append_valid_date(found_dates: list[date], year: int, month: int, day: int) -> None:
    try:
        found_dates.append(date(year, month, day))
    except ValueError:
        return


def _dedupe_dates(found_dates: list[date]) -> list[date]:
    deduped = []
    seen = set()

    for item in found_dates:
        if item not in seen:
            deduped.append(item)
            seen.add(item)

    return deduped
