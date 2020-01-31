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

import cv2
from pynput.keyboard import Key, Listener
from pytesseract import pytesseract

import matplotlib.pyplot as plt

espeak_loc = r'C:\Program Files (x86)\eSpeak\command_line\espeak.exe'
full_screen = True
debug = False


class G:
    img = None
    run = True
    show_new_image_flag = False
    old_caught = False


def turn_off():
    G.run = False


def tts(text):
    subprocess.Popen([espeak_loc, text])


def show_image(to_show_img):
    G.img = to_show_img
    G.show_new_image_flag = True


def get_game_screenshot():
    hwnd = win32gui.FindWindow(None, "Temtem")
    rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    window_offset = math.floor(((rect[2] - rect[0]) - client_rect[2]) / 2)

    title_offset = 0 if full_screen else ((rect[3] - rect[1]) - client_rect[3]) - window_offset

    bbox = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

    temp_screen = np.array(ImageGrab.grab(bbox=bbox))

    rect = win32gui.GetWindowRect(hwnd)
    crop = (rect[0] + window_offset, rect[1] + title_offset, rect[2] - window_offset,
            rect[3] - window_offset)

    return temp_screen[crop[1]:crop[3], crop[0]:crop[2]]


X0, Y0 = 1920, 1080
Y, X, _ = get_game_screenshot().shape
# x, y0, dy, w, h, n = 595, 513, 60, 40, 22, 7
x, y0, dy, w, h, n = int(1463 * X / X0), int(376 * Y / Y0), int(39 * Y / Y0), int(38 * X / X0), int(19 * Y / Y0), 7
caught_data = [(int(1476 * X / X0), int(347 * Y / Y0), 100, 110),
               (int(1183 * X / X0), int(801 * Y / Y0), 27, 32)]  # x, y, h0, h1


def process_img(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return img[:, :, 2]


def crop_img(image, i):
    y = y0 + (dy * i)
    img2 = image[y:y + h, x:x + w]
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
    print("checking SV")
    start = time.time()

    image = process_img(get_game_screenshot())

    sv_cropped = [crop_img(image, x) for x in range(n)]

    if debug:
        for i in sv_cropped:
            show_image(i)
            waiting.wait(lambda: not show_new_image_flag)

    result = [read_sv(x) for x in sv_cropped]
    s = sum(result)

    print(f"took {round(time.time() - start, 2)}s")
    tts(f"'Total SV is {s}'")


def on_release(key):
    if key == Key.f9:
        tell_sv()
    elif key == Key.f10:
        show_image(cv2.cvtColor(get_game_screenshot(), cv2.COLOR_BGR2HSV))
    elif key == Key.f11:
        turn_off()


def start_check_for_capture():
    while G.run:
        im = cv2.cvtColor(get_game_screenshot(), cv2.COLOR_BGR2HSV)
        caught = functools.reduce(lambda a, b: a and b[2] < im[b[1]][b[0]][0] < b[3], caught_data, True)
        if caught and not G.old_caught:
            tts("Please wait while I calculate total SV")
            tell_sv()

        G.old_caught = caught
        time.sleep(.5)


if __name__ == "__main__":

    checker = threading.Thread(target=start_check_for_capture)
    checker.start()

    with Listener(
            on_release=on_release) as listener:
        print("When you capture a Temtem I'll calculate its total SV\nPress f11 to quit")
        while G.run:
            waiting.wait(lambda: G.show_new_image_flag or not G.run)
            if G.img is not None:
                plt.imshow(G.img, cmap='gray')
                plt.show()
                show_new_image_flag = False

    checker.join()
