import datetime
import json
from ical.calendar import Calendar
from ical.event import Event
from ical.calendar_stream import IcsCalendarStream

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

calendar = Calendar()

# Load events from output.json
with open("cache/output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data.get("results", []):
    # Parse start and end dates
    start = item.get("startDate")
    end = item.get("endDate")
    if start and end:
        # Convert ISO8601 to datetime
        dtstart = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
        dtend = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
    else:
        continue

    # Extract class code from calendarNameLocalizable.rawValue
    raw_value = item.get("calendarNameLocalizable", {}).get("rawValue", "")
    # Find substring after year and before first ' -'
    import re

    match = re.search(r":?\s*([A-Z]+\s*-*\d+[A-Z]*)\s*-", raw_value)
    if match:
        class_code = match.group(1).replace("-", " ").strip()
    else:
        class_code = raw_value
    title = item.get("title", "")
    summary = f"{class_code} - {title}" if class_code and title else title
    description = title
    categories = (
        [item.get("dynamicCalendarItemProps", {}).get("eventType", "")]
        if item.get("dynamicCalendarItemProps")
        else []
    )
    calendar_id = item.get("calendarId", "")
    url = (
        f"{secrets['url_base']}/ultra/courses/{calendar_id}/outline"
        if calendar_id
        else None
    )

    event = Event(
        dtstart=dtstart,
        dtend=dtend,
        summary=summary,
        description=description,
        categories=categories,
        url=url,
    )
    calendar.events.append(event)

# Export calendar to .ics file
with open("cache/calendar.ics", "w", encoding="utf-8") as ics_file:
    ics_file.write(IcsCalendarStream.calendar_to_ics(calendar))
