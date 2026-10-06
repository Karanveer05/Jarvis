import time
import pyautogui

from open_close_apps import open_item, close_app
from type_file import type_text
from ui_controller import UIController


ui = UIController()


def search_text(text):
    pyautogui.write(text, interval=0.03)
    pyautogui.press("enter")
    time.sleep(2)


def screenshot():
    image = pyautogui.screenshot()
    image.save("screenshot.png")
    print("Screenshot saved")


def media_action(action):

    if action == "volume_up":
        pyautogui.press("volumeup")

    elif action == "volume_down":
        pyautogui.press("volumedown")

    elif action == "mute":
        pyautogui.press("volumemute")

    elif action == "pause":
        pyautogui.press("playpause")

    elif action == "resume":
        pyautogui.press("playpause")

    elif action == "next":
        pyautogui.press("nexttrack")

    elif action == "previous":
        pyautogui.press("prevtrack")


def execute_command(command):

    action = command.get("action")
    value = command.get("value")

    print("Executing:", action, value)

    # ------------------------
    # OPEN
    # ------------------------

    if action == "open":

        result = open_item(value)

        print(result)

        time.sleep(2)

    # ------------------------
    # CLOSE
    # ------------------------

    elif action == "close":

        result = close_app(value)

        print(result)

    # ------------------------
    # TYPE
    # ------------------------

    elif action == "type":

        type_text(value)

    # ------------------------
    # SEARCH
    # ------------------------

    elif action == "search":

        search_text(value)

    # ------------------------
    # SCREENSHOT
    # ------------------------

    elif action == "screenshot":

        screenshot()

    # ------------------------
    # MEDIA
    # ------------------------

    elif action in [
        "volume_up",
        "volume_down",
        "mute",
        "unmute",
        "pause",
        "resume",
        "next",
        "previous"
    ]:

        media_action(action)

    # ------------------------
    # CLICK
    # ------------------------

    elif action == "click":

        print("UI click requested:", value)

    # ------------------------
    # MESSAGE
    # ------------------------

    elif action == "message":

        target = command.get("target")

        print(
            "Message requested:",
            target,
            value
        )

    # ------------------------
    # YOUTUBE / UI ACTIONS
    # ------------------------

    elif action in [
        "play",
        "like",
        "dislike",
        "subscribe",
        "comment",
        "download"
    ]:

        print(
            f"{action} requested",
            value
        )

    else:

        print(
            "Unknown action:",
            action
        )


def execute_commands(commands):

    for command in commands:

        execute_command(command)

        time.sleep(0.5)