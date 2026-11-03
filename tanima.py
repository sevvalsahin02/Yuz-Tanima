
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
YAS_LISTESI = ["0-2", "4-6", "8-12", "15-20", "25-32", "38-43", "48-53", "60+"]
CINSIYET_LISTESI = ["Erkek", "Kadin"]
ORTALAMA = (78.4263377603, 87.7689143744, 114.895847746)

son_konusma_zamanlari = {}
son_gorulme= {}


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
    yas_agi = cinsiyet_agi = None
    try:
        yas_agi = cv2.dnn.readNet("model/age_net.caffemodel", "model/age_deploy.prototxt")
        cinsiyet_agi = cv2.dnn.readNet("model/gender_net.caffemodel", "model/gender_deploy.prototxt")
    except Exception as e:
        print("Yas/cinsiyet modeli yuklenemedi:", e)

    kamera = kamera_ac()
    kare_sayaci = 0
    bilinmeyen_sayac=0
    son_duygu = "Notr"
    son_yas, son_cinsiyet = "", ""          
    yas_oylari = deque(maxlen=10)           
    cinsiyet_oylari = deque(maxlen=10)      
    gecmis = deque(maxlen=8)
    tanima_sayaci = {}
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
                        # Yaş ve cinsiyet (renkli kare gerekir, her 10 karede bir)
            if yas_agi is not None and cinsiyet_agi is not None and kare_sayaci % 10 == 0 and w > 60 and h > 60:
                try:
                    pay = int(0.2 * w)
                    x1, y1 = max(x - pay, 0), max(y - pay, 0)
                    x2, y2 = min(x + w + pay, kare.shape[1]), min(y + h + pay, kare.shape[0])
                    blob = cv2.dnn.blobFromImage(kare[y1:y2, x1:x2], 1.0, (227, 227), ORTALAMA, swapRB=False)

                    cinsiyet_agi.setInput(blob)
                    cinsiyet_oylari.append(int(np.argmax(cinsiyet_agi.forward()[0])))
                    yas_agi.setInput(blob)
                    yas_oylari.append(int(np.argmax(yas_agi.forward()[0])))

                    son_cinsiyet = CINSIYET_LISTESI[max(set(cinsiyet_oylari), key=cinsiyet_oylari.count)]
                    son_yas = YAS_LISTESI[max(set(yas_oylari), key=yas_oylari.count)]
                except Exception as e:
                    print("Yas/cinsiyet hatasi:", e)
            
            if uzaklik < esik:
                bilinmeyen_sayac = 0
                kisi_adi = ascii_yap(isimler[str(etiket)] if str(etiket) in isimler else isimler[etiket])
                tanima_sayaci[kisi_adi] = tanima_sayaci.get(kisi_adi, 0) + 1

                if tanima_sayaci[kisi_adi] < 5:
                    yazi, renk = "Kontrol ediliyor...", (0, 255, 255)
                else:
                    yazi, renk = f"{kisi_adi} ({uzaklik:.0f})", (0, 255, 0)

                    # Sesli anons: kisi bir sure gorunmeyip geri gelince
                    son = son_gorulme.get(kisi_adi)
                    if son is None or (simdi - son > 15):
                        seslendir(f"Hos geldin {kisi_adi}")
                    son_gorulme[kisi_adi] = simdi
            else:
                tanima_sayaci.clear()
                bilinmeyen_sayac += 1
                yazi, renk = f"Bilinmiyor ({uzaklik:.0f})", (0, 0, 255)
                if bilinmeyen_sayac >= 15 and ("bilinmiyor" not in son_konusma_zamanlari or (simdi - son_konusma_zamanlari["bilinmiyor"] > 10)):
                    son_konusma_zamanlari["bilinmiyor"] = simdi
                    seslendir("Dikkat yetkisiz kisi algilandi")

            
            cv2.rectangle(kare, (x, y), (x + w, y + h), renk, 2)
            cv2.putText(kare, yazi, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, renk, 2)
            
            
            if duygu_agi is not None:
                cv2.putText(kare, f"Duygu: {son_duygu}", (x, y + h + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            if son_yas:
                cv2.putText(kare, f"{son_cinsiyet}, yas {son_yas}", (x, y + h + 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)    

        cv2.imshow(PENCERE, kare)
        if cikis_istendi(PENCERE):
            break

    kamera.release()
    cv2.destroyAllWindows()