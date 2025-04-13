# src/utils/helpers.py
import time
import random
import logging

def human_delay(min_seconds=1.0, max_seconds=3.0):
    """Adds a random delay to mimic human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    # logging.debug(f"Applying delay: {delay:.2f} seconds")
    time.sleep(delay)

def human_like_scroll(driver, scroll_amount=None):
    """Scrolls the page down in a human-like way."""
    if scroll_amount is None:
        # Scroll a fraction of the window height
        window_height = driver.execute_script("return window.innerHeight")
        scroll_amount = random.randint(int(window_height * 0.4), int(window_height * 0.8))

    # Break scrolling into multiple small movements
    steps = random.randint(3, 7)
    total_scrolled = 0
    for i in range(steps):
        step_scroll = (scroll_amount // steps) + random.randint(-20, 20)
        driver.execute_script(f"window.scrollBy(0, {step_scroll})")
        total_scrolled += step_scroll
        time.sleep(random.uniform(0.1, 0.3))
    # logging.debug(f"Scrolled down by ~{total_scrolled} pixels.")