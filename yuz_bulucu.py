import cv2
import config


def _siniflandirici_yukle():
    if not config.CASCADE_YOLU.exists():
        raise FileNotFoundError(f"Cascade dosyası bulunamadı: {config.CASCADE_YOLU}")
    xml = config.CASCADE_YOLU.read_text(encoding="utf-8")
    depo = cv2.FileStorage(xml, cv2.FILE_STORAGE_READ | cv2.FILE_STORAGE_MEMORY)
    siniflandirici = cv2.CascadeClassifier()
    if not siniflandirici.read(depo.getFirstTopLevelNode()):
        raise RuntimeError("Cascade dosyası yüklenemedi. OpenCV sürümünü kontrol edin (requirements.txt).")
    return siniflandirici


_yuz_siniflandirici = _siniflandirici_yukle()


def yuzleri_bul(gri_kare):
    return _yuz_siniflandirici.detectMultiScale(
        gri_kare, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80)
    )


def yuzu_hazirla(gri_kare, kutu):
    x, y, w, h = kutu
    yuz = gri_kare[y:y + h, x:x + w]
    yuz = cv2.resize(yuz, config.YUZ_BOYUTU)
    return cv2.equalizeHist(yuz)


def kamera_ac():
    kamera = cv2.VideoCapture(config.KAMERA_NO)
    if not kamera.isOpened():
        raise RuntimeError("Kamera açılamadı. config.py içindeki KAMERA_NO değerini kontrol edin.")
    return kamera
