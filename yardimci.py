import os
import cv2
import numpy as np


_TR_HARFLER = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def ascii_yap(metin: str) -> str:
    return metin.translate(_TR_HARFLER)


def resim_oku(yol):
    veri = np.fromfile(str(yol), dtype=np.uint8)
    return cv2.imdecode(veri, cv2.IMREAD_GRAYSCALE)


def resim_kaydet(yol, resim):
    basarili, tampon = cv2.imencode(".jpg", resim)
    if basarili:
        tampon.tofile(str(yol))


def model_kaydet(tanimlayici, yol):
    eski = os.getcwd()
    try:
        os.chdir(yol.parent)
        tanimlayici.write(yol.name)
    finally:
        os.chdir(eski)


def model_yukle(tanimlayici, yol):
    eski = os.getcwd()
    try:
        os.chdir(yol.parent)
        tanimlayici.read(yol.name)
    finally:
        os.chdir(eski)


def cikis_istendi(pencere_adi):
    tus = cv2.waitKey(1) & 0xFF
    if tus in (ord("q"), ord("Q"), 27):
        return True
    return cv2.getWindowProperty(pencere_adi, cv2.WND_PROP_VISIBLE) < 1
