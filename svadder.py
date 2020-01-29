import math
import win32gui
from win32api import GetSystemMetrics

from PIL import ImageGrab
import numpy as np

import os

import cv2
import matplotlib
from gtts import gTTS
from pynput.keyboard import Key, Listener
from pytesseract import pytesseract

import matplotlib.pyplot as plt
from playsound import playsound

img = None
run = True
update = False
mp3_name = 'temp.mp3'
x, y0, dy, w, h, n = 595, 513, 60, 40, 22, 7


def get_game_screenshot():
    # initialization
    hwnd = win32gui.FindWindow(None, "Temtem")
    rect = win32gui.GetWindowRect(hwnd)
    clientRect = win32gui.GetClientRect(hwnd)
    windowOffset = math.floor(((rect[2] - rect[0]) - clientRect[2]) / 2)

    # titleOffset = ((rect[3] - rect[1]) - clientRect[3]) - windowOffset
    titleOffset = 0

    # saving the image
    bbox = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

    tempScreen = np.array(ImageGrab.grab(bbox=bbox))

    # tempScreen = cv2.cvtColor(tempScreen, cv2.COLOR_BGR2RGB)

    rect = win32gui.GetWindowRect(hwnd)
    crop = (rect[0] + windowOffset, rect[1] + titleOffset, rect[2] - windowOffset,
            rect[3] - windowOffset)

    return tempScreen[crop[1]:crop[3], crop[0]:crop[2]]


def mypause(interval):
    backend = plt.rcParams['backend']
    if backend in matplotlib.rcsetup.interactive_bk:
        figManager = matplotlib._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return


def on_release(key):
    global img, run, update

    if key == Key.f9:
        img = get_game_screenshot()

        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img = img[:, :, 2]
        print(img.shape)
        img2 = img

        s = 0
        for i in range(n):
            y = y0 + (dy * i)
            img2 = img[y:y + h, x:x + w]
            ret, img2 = cv2.threshold(img2, 220, 255, cv2.THRESH_BINARY_INV)
            img2 = cv2.resize(img2, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            text = pytesseract.image_to_string(img2, config='--psm 8 --oem 0 -c tessedit_char_whitelist=0123456789')

            try:
                s += int(text)
            except Exception:
                pass

        sound = gTTS(f'Total SV is {s}', lang='en', slow=False)

        if os.path.exists(mp3_name):
            os.remove(mp3_name)
        sound.save(mp3_name)
        playsound(mp3_name)

        update = True
    elif key == Key.f11:
        run = False


if __name__ == "__main__":
    with Listener(
            on_release=on_release) as listener:
        listener.join()

        # while run:
        #     if img is not None:
        #         if update:
        #             im = plt.imshow(img, cmap='gray')
        #             plt.ion()
        #             plt.show()
        #             update = False
        #         mypause(0.01)
