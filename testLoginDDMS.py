from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import traceback
import time


USERNAME = "alyaselvia_VUfPw9"
ACCESS_KEY = "J8f3xCpKwpHsqCEF8xWD"
APP_ID = "bs://db0d2fae4ab415d8051eec649a0cb566a89c424f"


def handle_notification_permission(driver):

    try:

        wait_popup = WebDriverWait(driver, 5)

        allow_btn = wait_popup.until(
            EC.element_to_be_clickable(
                (
                    AppiumBy.ID,
                    "com.android.permissioncontroller:id/permission_allow_button"
                )
            )
        )

        allow_btn.click()

        print("Notification permission handled")

    except:

        try:

            allow_btn = driver.find_element(
                AppiumBy.ID,
                "com.android.packageinstaller:id/permission_allow_button"
            )

            allow_btn.click()

            print("Notification permission handled")

        except:

            try:

                allow_btn = driver.find_element(
                    AppiumBy.XPATH,
                    "//*[@text='Allow' or @text='Izinkan']"
                )

                allow_btn.click()

                print("Notification permission handled")

            except:
                print("Notification permission not displayed")


def run_test(device_name, platform_version):

    driver = None

    try:

        options = UiAutomator2Options()

        options.set_capability("platformName", "Android")
        options.set_capability("deviceName", device_name)
        options.set_capability("platformVersion", platform_version)

        options.set_capability("autoGrantPermissions", True)

        options.set_capability("app", APP_ID)

        options.set_capability("bstack:options", {
            "userName": USERNAME,
            "accessKey": ACCESS_KEY,
            "projectName": "Mobile Demo",
            "buildName": "Build Test",
            "sessionName": f"Login Test - {device_name}"
        })

        driver = webdriver.Remote(
            "https://hub.browserstack.com/wd/hub",
            options=options
        )

        driver.implicitly_wait(10)

        print(f"[START] {device_name}")

        # sementara diperbesar untuk debugging
        wait = WebDriverWait(driver, 90)

        print("Waiting app launch...")
        time.sleep(30)

        handle_notification_permission(driver)
        handle_notification_permission(driver)

        print("Waiting page ready...")
        time.sleep(10)

        print("====================================")
        print("DEBUGGING BEFORE USERNAME")
        print("====================================")

        try:
            print("Current Activity:")
            print(driver.current_activity)
        except:
            pass

        try:
            driver.save_screenshot(
                f"before_username_{device_name.replace(' ','_')}.png"
            )
            print("Screenshot saved")
        except Exception as screenshot_error:
            print(f"Screenshot Error: {screenshot_error}")

        try:
            with open(
                f"before_username_{device_name.replace(' ','_')}.xml",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(driver.page_source)

            print("Page source saved")
        except Exception as source_error:
            print(f"Page Source Error: {source_error}")

        print("Searching Username...")

        # Input Username
        username = wait.until(
        EC.presence_of_element_located(
        (
            AppiumBy.XPATH,
            "(//android.widget.EditText)[1]"
        )
        )   
        )

        username.send_keys("admin-100002")

        # Input Password
        password = wait.until(
        EC.presence_of_element_located(
        (
            AppiumBy.XPATH,
            "(//android.widget.EditText)[2]"
        )
        )
        )

        password.send_keys("admin")

        # Klik Login
        login_button = wait.until(
        EC.element_to_be_clickable(
        (
            AppiumBy.XPATH,
            "//*[@content-desc='Masuk']"
        )
        )
        )

        login_button.click()

        print(f"[PASSED] Login berhasil pada {device_name}")

        try:
            driver.execute_script(
                'browserstack_executor: {"action":"setSessionStatus","arguments":{"status":"passed","reason":"Login berhasil"}}'
            )
        except:
            pass

        time.sleep(10)

    except Exception as e:

        print(f"[FAILED] {device_name}")
        print(str(e))

        traceback.print_exc()

        if driver:

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            try:
                driver.save_screenshot(
                    f"error_{device_name.replace(' ','_')}_{timestamp}.png"
                )
            except:
                pass

            try:
                with open(
                    f"page_source_{device_name.replace(' ','_')}_{timestamp}.xml",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
            except:
                pass

            try:
                driver.execute_script(
                    f'browserstack_executor: {{"action":"setSessionStatus","arguments":{{"status":"failed","reason":"{str(e)[:200]}"}}}}'
                )
            except:
                pass

    finally:

        if driver:
            try:
                driver.quit()
                print(f"[CLOSED] {device_name}")
            except Exception as quit_error:
                print(f"Quit Error {device_name}: {quit_error}")


devices = [
    ("Samsung Galaxy Note 9", "8.1"),
    ("Huawei P30", "9.0"),
    ("Xiaomi Redmi Note 9", "10.0"),
    ("Samsung Galaxy Tab S7", "11.0"),
    ("Google Pixel 6", "12.0"),
    ("Oneplus 11R", "13.0"),
    ("Google Pixel 8", "14.0"),
    ("Oneplus 13R", "15.0"),
    ("Samsung Galaxy S26", "16.0")
]

with ThreadPoolExecutor(max_workers=len(devices)) as executor:

    futures = [
        executor.submit(run_test, device, version)
        for device, version in devices
    ]

    for future in futures:
        try:
            future.result()
        except Exception as e:
            print(f"Thread Error: {e}")