import datetime
import json
import os
import re
from urllib.parse import urlencode
from ical.calendar import Calendar
from ical.event import Event
from ical.calendar_stream import IcsCalendarStream
from env_utils import load_env_file

load_env_file()


CALENDAR_OUTPUT_PATH = "cache/output.json"
GRADE_OUTPUT_PATH = "cache/output_batch_grades.json"
GRADE_URL_PATTERN = re.compile(
    r"^v1/courses/(?P<course_id>[^/]+)/gradebook/columns/(?P<column_id>[^/]+)/grades\?$"
)
GRADE_404_USER_PATTERN = re.compile(
    r"specified user\s+(?P<user_id>[^\s]+)\s+does not have a grade"
)
DEFAULT_GRADE_USER_ID = os.getenv("BLACKBOARD_USER_ID", "_1062825_1")


def parse_datetime(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_class_code(course_name: str) -> str:
    match = re.search(r":?\s*([A-Z]+\s*-*\d+[A-Z]*)\s*-", course_name)
    if match:
        return match.group(1).replace("-", " ").strip()
    return course_name


def extract_grade_key(relative_url: str) -> tuple[str, str] | None:
    match = GRADE_URL_PATTERN.match(relative_url)
    if not match:
        return None
    return match.group("course_id"), match.group("column_id")


def format_number(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def format_batch_entry_for_description(entry: dict) -> str:
    if entry.get("statusCode") == 404:
        return "STATUS: NOT SUBMITTED"

    body = entry.get("body")
    if not isinstance(body, dict):
        return "STATUS: UNKNOWN"

    results = body.get("results")
    if not isinstance(results, list) or not results:
        return "STATUS: UNKNOWN"

    first_result = results[0]
    if not isinstance(first_result, dict):
        return "STATUS: UNKNOWN"

    grade_status = first_result.get("status")
    if grade_status == "NEEDS_GRADING":
        return "STATUS: SUBMITTED, UNGRADED"

    if grade_status == "GRADED":
        display_grade = first_result.get("displayGrade")
        score_text = "N/A"
        if isinstance(display_grade, dict):
            score = display_grade.get("score")
            if score is not None:
                score_text = format_number(score)

        points_possible = first_result.get("pointsPossible")
        points_text = (
            format_number(points_possible)
            if points_possible is not None
            else "N/A"
        )

        return f"STATUS: GRADED, {score_text}/{points_text}"

    return "STATUS: UNKNOWN"


def extract_user_id_from_entry(entry: dict) -> str | None:
    body = entry.get("body")
    if not isinstance(body, dict):
        return None

    results = body.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        user_id = results[0].get("userId")
        if isinstance(user_id, str) and user_id:
            return user_id

    message = body.get("message")
    if isinstance(message, str):
        match = GRADE_404_USER_PATTERN.search(message)
        if match:
            return match.group("user_id")

    return None


def load_grade_lookup() -> dict[tuple[str, str], dict[str, str]]:
    if not os.path.exists(GRADE_OUTPUT_PATH):
        return {}

    with open(GRADE_OUTPUT_PATH, "r", encoding="utf-8") as batch_file:
        payload = json.load(batch_file)

    if isinstance(payload, list):
        responses = payload
    elif isinstance(payload, dict):
        responses = payload.get("responses", [])
    else:
        responses = []

    lookup: dict[tuple[str, str], dict[str, str]] = {}
    for entry in responses:
        if not isinstance(entry, dict):
            continue
        key = extract_grade_key(entry.get("relativeUrl", ""))
        if not key:
            continue
        lookup[key] = {
            "description": format_batch_entry_for_description(entry),
            "userId": extract_user_id_from_entry(entry) or DEFAULT_GRADE_USER_ID,
        }
    return lookup


calendar = Calendar()
url_base = os.getenv("BLACKBOARD_URL_BASE")
if not url_base:
    raise RuntimeError("BLACKBOARD_URL_BASE is not set in .env")

# Load events from output.json
with open(CALENDAR_OUTPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

grade_lookup = load_grade_lookup()

for item in data.get("results", []):
    # Parse start and end dates
    dtstart = parse_datetime(item.get("startDate"))
    dtend = parse_datetime(item.get("endDate"))
    if not dtstart or not dtend:
        continue

    # Extract class code from calendarNameLocalizable.rawValue
    raw_value = item.get("calendarNameLocalizable", {}).get("rawValue", "")
    class_code = extract_class_code(raw_value)

    title = item.get("title", "")
    summary = f"{class_code} - {title}" if class_code and title else title

    calendar_id = item.get("calendarId", "")
    item_source_id = item.get("itemSourceId", "")
    grade_output = grade_lookup.get((calendar_id, item_source_id), {})

    description = grade_output.get("description", title)

    grade_user_id = grade_output.get("userId", DEFAULT_GRADE_USER_ID)

    categories = (
        [item.get("dynamicCalendarItemProps", {}).get("eventType", "")]
        if item.get("dynamicCalendarItemProps")
        else []
    )
    url = None
    if calendar_id and item_source_id and grade_user_id:
        query = urlencode(
            {
                "columnId": item_source_id,
                "userId": grade_user_id,
                "courseId": calendar_id,
            }
        )
        url = f"{url_base}/ultra/courses/{calendar_id}/grades/grade-and-feedback?{query}"

    calendar_event = Event(
        dtstart=dtstart,
        dtend=dtend,
        summary=summary,
        description=description,
        categories=categories,
        url=url,
    )
    # The ical package uses a dynamic events container; getattr avoids static type noise.
    getattr(calendar, "events").append(calendar_event)

# Export calendar to .ics file
with open("cache/calendar.ics", "w", encoding="utf-8") as ics_file:
    ics_file.write(IcsCalendarStream.calendar_to_ics(calendar))
