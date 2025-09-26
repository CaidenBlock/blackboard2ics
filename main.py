import subprocess
import sys
import os


def run_get_cal_json():
	print("Fetching calendar JSON...")
	result = subprocess.run([sys.executable, "get_cal_json.py"], check=False)
	# Check for output.json and 401
	needs_cookie = False
	try:
		with open("cache/output.json", "r", encoding="utf-8") as f:
			data = f.read()
			if '401' in data or 'Unauthorized' in data:
				needs_cookie = True
	except FileNotFoundError:
		needs_cookie = True
	if needs_cookie:
		print("Auth error or missing output.json. Running cookie collector...")
		subprocess.run([sys.executable, "cookie_collect_driver.py"], check=True)
		print("Retrying calendar fetch...")
		subprocess.run([sys.executable, "get_cal_json.py"], check=True)

def run_make_cal_ics():
	print("Generating calendar.ics...")
	subprocess.run([sys.executable, "make_cal_ics.py"], check=True)

def run_push_file_to_gist():
	print("Pushing calendar.ics to Gist...")
	subprocess.run([sys.executable, "push_file_to_gist.py"], check=True)

if __name__ == "__main__":
	run_get_cal_json()
	run_make_cal_ics()
	run_push_file_to_gist()
