import requests
import json
import os
from env_utils import load_env_file

load_env_file()

# --- Config ---
TOKEN = os.getenv("GITHUB_GIST_ACCESS_TOKEN")  # Personal access token with "gist" scope
GIST_ID = os.getenv("GITHUB_GIST_ID")  # The Gist ID from the URL
FILENAME = "blackboard.ics"                   # The file name in the Gist
LOCAL_FILE = "cache/calendar.ics"               # Local path to your .ics file

# Debug prints and checks
if not TOKEN or not TOKEN.strip():
    print("ERROR: GitHub token is missing or empty. Check .env.")
else:
    print(f"Using token: {TOKEN[:6]}... (length: {len(TOKEN)})")
if not GIST_ID or not GIST_ID.strip():
    print("ERROR: Gist ID is missing or empty. Check .env.")
else:
    print(f"Using Gist ID: {GIST_ID}")
# --------------

with open(LOCAL_FILE, "r", encoding="utf-8") as f:
    ics_content = f.read()

url = f"https://api.github.com/gists/{GIST_ID}"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

payload = {
    "files": {
        FILENAME: {
            "content": ics_content
        }
    }
}

resp = requests.patch(url, headers=headers, data=json.dumps(payload), timeout=15)

if resp.status_code == 200:
    print("Gist updated successfully.")
else:
    print("Error:", resp.status_code, resp.text)
