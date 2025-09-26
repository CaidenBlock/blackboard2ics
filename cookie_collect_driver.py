import json
import time
import pyotp
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


COOKIES_FILE = "cache/response_cookies.json"
SECRETS_FILE = "secrets.json"
with open(SECRETS_FILE, "r", encoding="utf-8") as f:
    secrets = json.load(f)

# Configure headless Firefox
options = Options()
options.headless = True
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


def collect_cookies():
    # Load secrets
    username = secrets["username"]
    password = secrets["password"]
    totp_key = secrets.get("totp_key")

    driver = webdriver.Firefox(options=options)
    driver.get(secrets["login_url"])
    time.sleep(2)

    # Enter username
    user_input = driver.find_element(By.XPATH, '//*[@id="i0116"]')
    user_input.send_keys(username)
    user_input.send_keys(Keys.ENTER)
    time.sleep(1)

    # Enter password
    pass_input = driver.find_element(By.XPATH, '//*[@id="i0118"]')
    pass_input.send_keys(password)
    pass_input.send_keys(Keys.ENTER)
    time.sleep(3)

    # If TOTP key is provided, generate and enter code
    if totp_key:
        totp = pyotp.TOTP(totp_key)
        code = totp.now()
        print(f"Generated TOTP code: {code}")
        try:
            totp_input = driver.find_element(By.XPATH, '//*[@id="idTxtBx_SAOTCC_OTC"]')
            totp_input.send_keys(code)
            totp_input.send_keys(Keys.ENTER)
            time.sleep(2)
        except Exception as e:
            print(f"Could not find TOTP input field: {e}")
            input(
                "If you need to enter a code manually, do so now and press Enter to continue..."
            )
    else:
        print("Waiting for authentication step (e.g., passkey or MFA)...")
        input("Complete authentication, then press Enter to continue...")

    confirm_btn = driver.find_element(By.XPATH, '//*[@id="idSIButton9"]')
    confirm_btn.send_keys(Keys.ENTER)
    time.sleep(2)
    # Wait for BbRouter cookie
    print("Waiting for BbRouter cookie...")
    max_wait = 120  # seconds
    interval = 2
    waited = 0
    while waited < max_wait:
        cookies = driver.get_cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
        if "BbRouter" in cookies_dict:
            print("BbRouter cookie found!")
            break
        time.sleep(interval)
        waited += interval
    else:
        print("BbRouter cookie not found after waiting. Saving current cookies.")
    # cookies_dict["BbClientCalenderTimeZone"] = "America/Chicago"
    with open(COOKIES_FILE, "w", encoding="utf-8") as cookies_file:
        json.dump(cookies_dict, cookies_file, indent=4, ensure_ascii=False)
    print(f"Cookies saved to {COOKIES_FILE}")
    driver.quit()


if __name__ == "__main__":
    collect_cookies()
