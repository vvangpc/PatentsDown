from downloader import init_driver
import traceback

def test_logger(msg):
    print(f"TEST_LOG: {msg}")

print("Testing webdriver initialization...")
try:
    driver = init_driver(log_callback=test_logger)
    if driver:
        print("Success! Driver initialized.")
        driver.quit()
    else:
        print("Driver returned None.")
except Exception as e:
    print(f"Exception escaped init_driver: {e}")
    traceback.print_exc()
