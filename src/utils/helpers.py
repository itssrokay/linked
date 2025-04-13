# src/utils/helpers.py
import time
import random

# Directly copied from the provided code
def human_delay(min_seconds=1.0, max_seconds=3.0):
    """Adds a random delay to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

# Directly copied from the provided code
def human_like_scroll(driver, scroll_amount=None):
    """Scrolls the page in a human-like way."""
    if scroll_amount is None:
        scroll_amount = random.randint(300, 700)

    # Break scrolling into multiple small movements
    steps = random.randint(3, 7)
    for i in range(steps):
        step_scroll = scroll_amount // steps
        variation = random.randint(-20, 20)  # Add some variation
        driver.execute_script(f"window.scrollBy(0, {step_scroll + variation})")
        time.sleep(random.uniform(0.1, 0.3))