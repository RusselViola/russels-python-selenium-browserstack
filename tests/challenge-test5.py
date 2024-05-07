import os
import json
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Generate a unique build name with the current date and time
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
build_name = f"Test Build - {current_time}"

# set up Chrome options
chrome_options = ChromeOptions()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option('w3c', True)

mobile_chrome_options = ChromeOptions()
mobile_chrome_options.add_experimental_option("mobileEmulation", {"deviceName": "Samsung Galaxy S22"})

# set up Firefox options
firefox_options = FirefoxOptions()
firefox_options.add_argument("--width=1920")
firefox_options.add_argument("--height=1080")

# Retrieve BrowserStack credentials from environment variables
bs_username = os.environ.get("BROWSERSTACK_USERNAME")
access_key = os.environ.get("BROWSERSTACK_ACCESS_KEY")

if not bs_username or not access_key:
    raise ValueError("BrowserStack credentials not set in environment")

# # Configuration
browserstack_url = "https://www.browserstack.com"
username = os.environ.get("BS_CREDS_USR")  # Replace with your actual username
password = os.environ.get("BS_CREDS_PSW")  # Replace with your actual password

if not username or not password:
    raise ValueError("Trial credentials not set in environment")

# Setup Chrome Options for Desktop
chrome_options = ChromeOptions()
chrome_options.set_capability("bstack:options", {
    "os": "Windows",
    "osVersion": "10",
    "sessionName": "Windows 10 Chrome Test",
    "buildName": build_name,
    "projectName": "Multi-Browser Testing",
    "userName": bs_username,
    "accessKey": access_key
})
chrome_options.add_argument("--window-size=1920,1080")

# Setup Chrome Options for Mobile (Samsung Galaxy S22)
mobile_chrome_options = ChromeOptions()
mobile_chrome_options.set_capability("bstack:options", {
    "deviceName": "Samsung Galaxy S22",
    "osVersion": "12.0",
    "sessionName": "Samsung Galaxy Test",
    "buildName": build_name,
    "projectName": "Multi-Browser Testing",
    "userName": bs_username,
    "accessKey": access_key
})
mobile_chrome_options.add_argument("--window-size=360,640")  # Emulating a smaller device screen

# Setup Firefox Options
firefox_options = FirefoxOptions()
firefox_options.set_capability("bstack:options", {
    "os": "OS X",
    "osVersion": "Ventura",
    "sessionName": "Mac Firefox Test",
    "buildName": build_name,
    "projectName": "Multi-Browser Testing",
    "userName": bs_username,
    "accessKey": access_key
})
firefox_options.add_argument("--width=1920")
firefox_options.add_argument("--height=1080")

# Browser configurations as a list of options
browser_options_list = [chrome_options, firefox_options, mobile_chrome_options]

def run_tests_on_browserstack():
    for options in browser_options_list:
        # Initialize the WebDriver for each browser configuration
        driver = webdriver.Remote(
            command_executor=f'https://{username}:{access_key}@hub-cloud.browserstack.com/wd/hub',
            options=options
        )
        
        try:
            # Your test code here
            driver.get("http://www.browserstack.com")
            bstack_options = options.capabilities.get("bstack:options", {})
            os_version = bstack_options.get("osVersion", "N/A")
            os_name = bstack_options.get("os", "N/A")
            device_name = bstack_options.get("deviceName", "No Device Specified")
            browser_name = options.capabilities.get("browserName", "Unknown Browser")
            print(f"Testing on {os_name} {os_version} {device_name} with {browser_name}: {driver.title}")

            # Function to handle the dynamic finding of elements that might be hidden
            def find_element_with_fallback(search_type, identifier, fallback_search_type, fallback_identifier):
                elements = driver.find_elements(search_type, identifier)
                if not elements:
                    print(f"{identifier} not initially found. Checking for primary menu toggle.")
                    primary_menu_toggles = driver.find_elements(fallback_search_type, fallback_identifier)
                    if primary_menu_toggles:
                        print("Primary menu toggle found. Clicking on it.")
                        primary_menu_toggles[0].click()
                        # Wait a bit for the menu to expand and reveal the needed element
                        return WebDriverWait(driver, 10).until(EC.visibility_of_element_located((search_type, identifier)))
                    else:
                        print("Primary menu toggle not found. Cannot proceed.")
                        raise Exception(f"Failed to find {identifier} and primary menu toggle.")
                else:
                    print(f"{identifier} found. Proceeding.")
                    return elements[0]

            # Find and click the Sign in button
            sign_in_button = find_element_with_fallback(By.LINK_TEXT, "Sign in", By.ID, "primary-menu-toggle")
            sign_in_button.click()

            # Login process
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "user_email_login"))).send_keys(username)
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "user_password"))).send_keys(password + Keys.RETURN)

            # Wait for login to complete and homepage to load
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, "DASHBOARD")))

            # Find and assert 'Invite Team' link
            invite_link = find_element_with_fallback(By.ID, "invite-link", By.ID, "primary-menu-toggle")
            assert invite_link, "Invite Users link not found on the homepage."

            # Get and print the link's URL
            invite_link_url = invite_link.get_attribute('href')
            print(f"Invite Team Link URL: {invite_link_url}")

            # Logout sequence
            primary_menu_toggles = driver.find_elements(By.ID, "primary-menu-toggle")
            if primary_menu_toggles and primary_menu_toggles[0].is_displayed():
                print("Clicking primary menu toggle to access account options.")
                primary_menu_toggles[0].click()
            else:
                print("Primary menu toggle not found. Looking for account menu.")
                account_menu_toggles = driver.find_elements(By.ID, "account-menu-toggle")
                print("Account menu toggle found. Clicking to access logout.")
                account_menu_toggles[0].click()

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Sign out"))).click()
            print(f"Signing out")
            driver.execute_script(
                    'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Successfully completed all actions."}}')

        except NoSuchElementException as err:
            message = 'Exception: ' + str(err.__class__) + str(err.msg)
            driver.execute_script(
                'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')

        except Exception as err:
            message = 'Exception: ' + str(err.__class__) + str(err.msg)
            driver.execute_script(
                'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": ' + json.dumps(message) + '}}')

        finally:
            # Cleanup
            driver.quit()
# Run the tests
run_tests_on_browserstack()