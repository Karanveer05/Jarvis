import pyautogui
import time

def type_text(text):
    pyautogui.write(text, interval=0.03)

def main():
    text = input("What do you want to type? ")
    time.sleep(1)
    type_text(text)

if __name__ == "__main__":
    main()