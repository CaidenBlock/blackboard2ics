import subprocess
import sys


def run_get_cal_json():
    print("Fetching calendar JSON...")
    result = subprocess.run([sys.executable, "get_cal_json.py"], check=False)
    if result.returncode == 10:
        print("401 received. Running cookie collector...")
        subprocess.run([sys.executable, "cookie_collect_driver.py"], check=True)
        print("Retrying calendar fetch...")
        subprocess.run([sys.executable, "get_cal_json.py"], check=True)
    elif result.returncode != 0:
        raise RuntimeError(f"get_cal_json.py failed with exit code {result.returncode}")


def run_batch_get_grades():
    print("Fetching assignment grades via batch request...")
    result = subprocess.run([sys.executable, "batch_get_grades.py"], check=False)
    if result.returncode == 10:
        print("401 received during batch grade fetch. Running cookie collector...")
        subprocess.run([sys.executable, "cookie_collect_driver.py"], check=True)
        print("Refreshing calendar JSON...")
        subprocess.run([sys.executable, "get_cal_json.py"], check=True)
        print("Retrying batch grade fetch...")
        subprocess.run([sys.executable, "batch_get_grades.py"], check=True)
    elif result.returncode != 0:
        raise RuntimeError(
            f"batch_get_grades.py failed with exit code {result.returncode}"
        )


def run_make_cal_ics():
    print("Generating calendar.ics...")
    subprocess.run([sys.executable, "make_cal_ics.py"], check=True)

def run_push_file_to_gist():
    print("Pushing calendar.ics to Gist...")
    subprocess.run([sys.executable, "push_file_to_gist.py"], check=True)

if __name__ == "__main__":
    run_get_cal_json()
    run_batch_get_grades()
    run_make_cal_ics()
    run_push_file_to_gist()
