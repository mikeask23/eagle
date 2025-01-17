from pynput import keyboard
import asyncio

def on_press(key, screenshot_callback, next_url_event):
    """Handles key presses for screenshot and next URL."""
    try:
        if key.char == 's':
            print("Taking screenshot...")
            screenshot_callback()  # Add screenshot request to the queue
        elif key.char == 'n':
            print("Requesting next URL...")
            next_url_event.set()  # Signal to move to the next URL
    except AttributeError:
        pass  # Ignore special keys

def start_input_listener(screenshot_callback, next_url_event):
    """Starts the keyboard listener to capture user input."""
    with keyboard.Listener(on_press=lambda key: on_press(key, screenshot_callback, next_url_event)) as listener:
        listener.join()