import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
browserstack_url = "https://www.browserstack.com"
username = os.getenv('BSTACK_TRIAL_USERNAME')  # Replace with your actual username
password = os.getenv('BSTACK_TRIAL_PASSWORD')  # Replace with your actual password

# Setup WebDriver
driver = webdriver.Chrome()  # Replace with your browser's driver if not using Chrome
driver.get(browserstack_url)

try:
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
    # Close the browser
    driver.quit()