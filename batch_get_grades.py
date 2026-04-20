import os
import json
import sys
from datetime import datetime, timedelta, timezone
import requests
from env_utils import load_env_file

load_env_file()


CALENDAR_OUTPUT_PATH = "cache/output.json"
BATCH_OUTPUT_PATH = "cache/output_batch_grades.json"


def read_non_negative_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise RuntimeError(f"{name} must be >= 0")
    return parsed


def parse_blackboard_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_xsrf_token(cookies: dict[str, str]) -> str | None:
    xsrf_token = cookies.get("xsrf")
    if xsrf_token:
        return xsrf_token

    bb_router = cookies.get("BbRouter", "")
    for item in bb_router.split(","):
        item = item.strip()
        if item.startswith("xsrf:"):
            return item.split(":", 1)[1]
    return None


def build_batch_body(
    calendar_items: list[dict], window_start: datetime, window_end: datetime
) -> tuple[list[dict], list[dict]]:
    body: list[dict] = []
    selected_assignments: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for item in calendar_items:
        due_at = parse_blackboard_datetime(item.get("endDate") or item.get("startDate"))
        if due_at is None or due_at < window_start or due_at > window_end:
            continue

        course_id = item.get("calendarId")
        column_id = item.get("itemSourceId")
        source_type = item.get("itemSourceType", "")

        if not course_id or not column_id:
            continue
        if source_type and source_type != "blackboard.platform.gradebook2.GradableItem":
            continue

        key = (course_id, column_id)
        if key in seen:
            continue
        seen.add(key)

        relative_url = f"v1/courses/{course_id}/gradebook/columns/{column_id}/grades?"
        body.append({"method": "GET", "relativeUrl": relative_url})
        selected_assignments.append(
            {
                "courseId": course_id,
                "columnId": column_id,
                "title": item.get("title", ""),
                "endDate": item.get("endDate"),
                "relativeUrl": relative_url,
            }
        )

    return body, selected_assignments


def write_batch_output(payload: dict) -> None:
    os.makedirs("cache", exist_ok=True)
    with open(BATCH_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def main():
    url_base = os.getenv("BLACKBOARD_URL_BASE")
    if not url_base:
        raise RuntimeError("BLACKBOARD_URL_BASE is not set in .env")

    url = f"{url_base}/learn/api/v1/utilities/batch"

    params = {
        "xb": "0",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    if not os.path.exists(CALENDAR_OUTPUT_PATH):
        raise RuntimeError(
            "cache/output.json was not found. Run get_cal_json.py before batch_get_grades.py"
        )

    with open(CALENDAR_OUTPUT_PATH, "r", encoding="utf-8") as output_file:
        output_data = json.load(output_file)

    calendar_items = output_data.get("results", []) if isinstance(output_data, dict) else []

    lookback_days = read_non_negative_int_env("GRADE_BATCH_LOOKBACK_DAYS", 1)
    lookahead_days = read_non_negative_int_env("GRADE_BATCH_LOOKAHEAD_DAYS", 7)
    now_utc = datetime.now(timezone.utc)
    window_start = now_utc - timedelta(days=lookback_days)
    window_end = now_utc + timedelta(days=lookahead_days)

    body, selected_assignments = build_batch_body(calendar_items, window_start, window_end)

    if not body:
        write_batch_output(
            {
                "generatedAt": now_utc.isoformat(),
                "window": {
                    "lookbackDays": lookback_days,
                    "lookaheadDays": lookahead_days,
                    "start": window_start.isoformat(),
                    "end": window_end.isoformat(),
                },
                "requests": [],
                "selectedAssignments": [],
                "responses": [],
            }
        )
        print(
            "No assignments in the configured range; wrote empty cache/output_batch_grades.json"
        )
        return 0

    # Load cookies from previous response if available
    cookies = {}
    if os.path.exists("cache/response_cookies.json"):
        with open("cache/response_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)

    xsrf_token = extract_xsrf_token(cookies)

    if xsrf_token:
        headers["X-Blackboard-XSRF"] = xsrf_token

    # Always ensure BbClientCalenderTimeZone is present
    cookies["BbClientCalenderTimeZone"] = "America/Chicago"

    response = requests.put(
        url,
        headers=headers,
        params=params,
        json=body,
        cookies=cookies,
        timeout=10,
    )

    if response.status_code == 401:
        print("401 Unauthorized. Please log in via the browser to collect cookies.")
        # Optionally, re-load cookies from browser or prompt user to export cookies to response_cookies.json
        print(
            "Please export your cookies to response_cookies.json and rerun the script."
        )
        return 10

    try:
        data = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        data = response.text

    write_batch_output(
        {
            "generatedAt": now_utc.isoformat(),
            "window": {
                "lookbackDays": lookback_days,
                "lookaheadDays": lookahead_days,
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
            },
            "requests": body,
            "selectedAssignments": selected_assignments,
            "responses": data if isinstance(data, list) else [],
            "rawResponse": data if not isinstance(data, list) else None,
        }
    )

    # Save response cookies to a separate file
    # cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
    # with open("cache/response_cookies.json", "w", encoding="utf-8") as f:
    #    json.dump(cookies_dict, f, indent=4, ensure_ascii=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
