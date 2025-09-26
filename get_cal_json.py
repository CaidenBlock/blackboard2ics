import os
import json
import requests

with open("secrets.json", "r", encoding="utf-8") as secrets_file:
    secrets = json.load(secrets_file)


def main():

    url = f"{secrets['url_base']}/learn/api/v1/calendars/dueDateCalendarItems"

    params = {
        "limit": "9999",
        "date": "2025-09-18",
        "date_compare": "greaterOrEqual",
        "includeCount": "true",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Accept": "application/json",
    }

    # Load cookies from previous response if available
    cookies = {}
    if os.path.exists("cache/response_cookies.json"):
        with open("cache/response_cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
    # Always ensure BbClientCalenderTimeZone is present
    cookies["BbClientCalenderTimeZone"] = "America/Chicago"

    response = requests.get(
        url, headers=headers, params=params, cookies=cookies, timeout=10
    )

    if response.status_code == 401:
        print("401 Unauthorized. Please log in via the browser to collect cookies.")
        # Optionally, re-load cookies from browser or prompt user to export cookies to response_cookies.json
        print(
            "Please export your cookies to response_cookies.json and rerun the script."
        )
        return

    try:
        data = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        data = response.text
    with open("cache/output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Save response cookies to a separate file
    cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
    with open("cache/response_cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies_dict, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
