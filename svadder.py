import functools
import math
import subprocess
import threading
import time
import win32gui
from win32api import GetSystemMetrics

import waiting
from PIL import ImageGrab
import numpy as np

import os

import cv2
import matplotlib
from pynput.keyboard import Key, Listener
from pytesseract import pytesseract

import matplotlib.pyplot as plt

img = None
run = True
show_new_image_flag = False
debug = False
old_caught = False
mp3_name = 'temp.mp3'
espeak_loc = r'C:\Program Files (x86)\eSpeak\command_line\espeak.exe'

# x, y0, dy, w, h, n = 595, 513, 60, 40, 22, 7
x, y0, dy, w, h, n = 1463, 376, 39, 38, 19, 7
caught_data = [(1476, 347, 100, 110), (1183, 801, 27, 32)]  # x, y, h0, h1


def toggle_debug():
    global debug
    debug = not debug


def turn_off():
    global run
    run = False


def tts(text):
    subprocess.Popen([espeak_loc, text])


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


def process_img(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return img[:, :, 2]


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


def crop_img(i):
    y = y0 + (dy * i)
    img2 = img[y:y + h, x:x + w]
    return img2


# noinspection PyBroadException
def read_sv(img2):
    try:
        ret, img2 = cv2.threshold(img2, 220, 255, cv2.THRESH_BINARY_INV)
        img2 = cv2.resize(img2, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        text = pytesseract.image_to_string(img2, config='--psm 8 --oem 0 -c tessedit_char_whitelist=0123456789')
        return int(text)
    except Exception:
        print("there was en error reading svs")
        return 0


def tell_sv():
    global img, run, show_new_image_flag

    print("checking SV")
    start = time.time()

    img = process_img(get_game_screenshot())

    sv_cropped = [crop_img(x) for x in range(n)]

    if debug:
        for i in sv_cropped:
            show_image(i)
            waiting.wait(lambda: not show_new_image_flag)

    result = [read_sv(x) for x in sv_cropped]
    s = sum(result)

    print(f"took {round(time.time() - start, 2)}s")
    tts(f"'Total SV is {s}'")


def show_image(to_show_img):
    global img, show_new_image_flag

    img = to_show_img
    show_new_image_flag = True


def on_release(key):
    global show_new_image_flag

    if key == Key.f8:
        toggle_debug()
        print(f"Debug is turned {'on' if debug else 'off'}")
    if key == Key.f9:
        tell_sv()
    elif key == Key.f10:
        show_image(cv2.cvtColor(get_game_screenshot(), cv2.COLOR_BGR2HSV))
    elif key == Key.f11:
        turn_off()


def start_check_for_capture():
    global old_caught

    while run:
        im = cv2.cvtColor(get_game_screenshot(), cv2.COLOR_BGR2HSV)
        caught = functools.reduce(lambda a, b: a and b[2] < im[b[1]][b[0]][0] < b[3], caught_data, True)
        if caught and not old_caught:
            tts("Please wait while I calculate total SV")
            tell_sv()

        old_caught = caught
        time.sleep(.5)


if __name__ == "__main__":
    checker = threading.Thread(target=start_check_for_capture)
    checker.start()

    with Listener(
            on_release=on_release) as listener:
        print("ready")
        while run:
            waiting.wait(lambda: show_new_image_flag)
            plt.imshow(img, cmap='gray')
            plt.show()
            show_new_image_flag = False

    checker.join()
