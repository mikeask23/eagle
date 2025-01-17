import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from utils.dolphin_anty_utils import authorize_dolphin_anty, launch_profile
from utils.page_processing import process_page
from utils.user_input_utils import start_input_listener
from utils.screenshot_utils import take_screenshot
import threading

async def main():
    """Main function to run the script."""
    profile_id = "547791748"  # Replace with your Dolphin Anty profile ID

    load_dotenv()
    api_token = os.getenv("DOLPHIN_ANTY_TOKEN")

    if not api_token or not await authorize_dolphin_anty(api_token):
        return

    port, ws_endpoint = await launch_profile(profile_id)
    if not port or not ws_endpoint:
        return

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"ws://127.0.0.1:{port}{ws_endpoint}")
        context = browser.contexts[0]
        page = await context.new_page()

        try:
            with open("urls.txt", "r") as f:
                urls = [line.strip() for line in f]
        except FileNotFoundError:
            print("Error: urls.txt not found.")
            return

        # Create an event to signal moving to the next URL
        next_url_event = asyncio.Event()

        # Create a queue to hold screenshot requests
        screenshot_queue = asyncio.Queue()

        def screenshot_callback():
            """Callback to add screenshot request to the queue."""
            screenshot_queue.put_nowait(page.url)

        # Start the keyboard listener thread
        listener_thread = threading.Thread(
            target=start_input_listener,
            args=(screenshot_callback, next_url_event),
            daemon=True
        )
        listener_thread.start()

        async def process_screenshots():
            """Process screenshots from the queue."""
            while True:
                url = await screenshot_queue.get()
                if url == "quit":  # Signal to stop processing screenshots
                    break
                await take_screenshot(page, url)
                screenshot_queue.task_done()

        # Start the screenshot processing task
        screenshot_task = asyncio.create_task(process_screenshots())

        for url in urls:
            # Reset the event for each URL
            next_url_event.clear()
            await process_page(page, url, next_url_event)

        # Stop the screenshot processing task
        await screenshot_queue.put("quit")
        await screenshot_task

        await context.close()
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")