
import json
import threading
import time
from pathlib import Path
import cv2
import numpy as np
from collections import deque

import config
from egitim import tanimlayici_olustur
from yardimci import ascii_yap, cikis_istendi, model_yukle
from yuz_bulucu import kamera_ac, yuzleri_bul, yuzu_hazirla

PENCERE = "Yuz Tanima (cikis: q veya ESC)"

AGIRLIK = np.array([0.6, 1.0, 1.0, 1.8, 1.8, 1.5, 1.5, 1.2])

DUYGU_LISTESI = [
    "Notr",
    "Mutlu",
    "Saskin",
    "Uzgun",
    "Sinirli",
    "Igrenmis",
    "Korkmus",
    "Kucumseme"
]

son_konusma_zamanlari = {}


def seslendir(metin: str):
    
    def _konus():
        try:
            import pythoncom 
            pythoncom.CoInitialize()  # Windows thread ses motoru başlatıcısı
            import pyttsx3
            motor = pyttsx3.init()
            motor.setProperty("rate", 140)  # Konuşma hızı
            motor.say(metin)
            motor.runAndWait()
        except Exception as e:
            print("Seslendirme Hatası:", e)

    threading.Thread(target=_konus, daemon=True).start()


def tani():
    
    if not config.MODEL_YOLU.exists():
        raise FileNotFoundError("Model bulunamadı. Önce 'Modeli Eğit' düğmesine basın.")

    tanimlayici = tanimlayici_olustur()
    model_yukle(tanimlayici, config.MODEL_YOLU)
    with open(config.ETIKET_YOLU, encoding="utf-8") as f:
        isimler = json.load(f)
    esik = config.ESIK[config.ALGORITMA]

    
    duygu_agi = None
    duygu_yolu = Path("duygu_modeli.onnx")
    if duygu_yolu.exists():
        try:
            duygu_agi = cv2.dnn.readNetFromONNX(str(duygu_yolu))
        except Exception:
            duygu_agi = None

    kamera = kamera_ac()
    kare_sayaci = 0
    bilinmeyen_sayac=0
    son_duygu = "Notr"
    gecmis = deque(maxlen=8)
    while True:
        basarili, kare = kamera.read()
        if not basarili:
            break
        kare_sayaci += 1
        gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
        simdi = time.time()

        for kutu in yuzleri_bul(gri):
            x, y, w, h = kutu
            etiket, uzaklik = tanimlayici.predict(yuzu_hazirla(gri, kutu))

            
            if duygu_agi is not None and kare_sayaci % 3 == 0 and w > 40 and h > 40:
                try:
                        
                    pay = int(0.1 * w)  # alın ve çene de görünsün
                    x1, y1 = max(x - pay, 0), max(y - pay, 0)
                    x2, y2 = min(x + w + pay, gri.shape[1]), min(y + h + pay, gri.shape[0])
                    yuz_yeniden = cv2.resize(gri[y1:y2, x1:x2], (64, 64))
                    blob = cv2.dnn.blobFromImage(yuz_yeniden, 1.0, (64, 64), (0,), False, False)
                    duygu_agi.setInput(blob)
                    ciktilar = duygu_agi.forward()[0].flatten()

                    olasilik = np.exp(ciktilar - ciktilar.max())
                    olasilik /= olasilik.sum()
                    olasilik = olasilik * AGIRLIK      
                    olasilik /= olasilik.sum()

                    gecmis.append(olasilik)           
                    ortalama = np.mean(gecmis, axis=0)
                    son_duygu = DUYGU_LISTESI[int(np.argmax(ortalama))]
                except Exception as e:
                    print("Duygu hatası:", e)

            
            if uzaklik < esik:
                bilinmeyen_sayac=0
                kisi_adi = ascii_yap(isimler[str(etiket)] if str(etiket) in isimler else isimler[etiket])
                yazi, renk = f"{kisi_adi} ({uzaklik:.0f})", (0, 255, 0)

                # Sesli anons
                if kisi_adi not in son_konusma_zamanlari or (simdi - son_konusma_zamanlari[kisi_adi] > 8):
                    son_konusma_zamanlari[kisi_adi] = simdi
                    seslendir(f"Hos geldin {kisi_adi}")
            else:
                bilinmeyen_sayac += 1
                yazi, renk = f"Bilinmiyor ({uzaklik:.0f})", (0, 0, 255)
                if bilinmeyen_sayac >= 15 and ("bilinmiyor" not in son_konusma_zamanlari or (simdi - son_konusma_zamanlari["bilinmiyor"] > 10)):
                    son_konusma_zamanlari["bilinmiyor"] = simdi
                    seslendir("Dikkat yetkisiz kisi algilandi")

            
            cv2.rectangle(kare, (x, y), (x + w, y + h), renk, 2)
            cv2.putText(kare, yazi, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, renk, 2)
            
            
            if duygu_agi is not None:
                cv2.putText(kare, f"Duygu: {son_duygu}", (x, y + h + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.imshow(PENCERE, kare)
        if cikis_istendi(PENCERE):
            break

    kamera.release()
    cv2.destroyAllWindows()