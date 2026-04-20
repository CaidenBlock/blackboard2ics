import os
import json
import sys
import requests
from env_utils import load_env_file

load_env_file()


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

    body = [
        {
            "method": "GET",
            "relativeUrl": "v1/courses/_360315_1/gradebook/columns/_3446217_1/grades?",
        },
        {
            "method": "GET",
            "relativeUrl": "v1/courses/_361095_1/gradebook/columns/_3446147_1/grades?",
        },
    ]

    # Load cookies from previous response if available
    cookies = {}
    if os.path.exists("cache/response_cookies.json"):
        with open("cache/response_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)

    xsrf_token = cookies.get("xsrf")
    if not xsrf_token:
        bb_router = cookies.get("BbRouter", "")
        for item in bb_router.split(","):
            item = item.strip()
            if item.startswith("xsrf:"):
                xsrf_token = item.split(":", 1)[1]
                break

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
    with open("cache/output_test.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Save response cookies to a separate file
    # cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
    # with open("cache/response_cookies.json", "w", encoding="utf-8") as f:
    #    json.dump(cookies_dict, f, indent=4, ensure_ascii=False)

    return 0


if __name__ == "__main__":
    sys.exit(main())
