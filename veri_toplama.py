
import time
import cv2
import config
from yardimci import resim_kaydet, ascii_yap, cikis_istendi
from yuz_bulucu import yuzleri_bul, yuzu_hazirla, kamera_ac

PENCERE = "Veri Toplama"


def veri_topla(isim: str) -> int:
    kisi_klasoru = config.VERI_KLASORU / isim
    kisi_klasoru.mkdir(parents=True, exist_ok=True)
    mevcut = len(list(kisi_klasoru.glob("*.jpg")))  

    kamera = kamera_ac()
    kaydedilen = 0
    son_kayit = 0.0

    while kaydedilen < config.FOTO_SAYISI:
        basarili, kare = kamera.read()
        if not basarili:
            break
        gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
        yuzler = yuzleri_bul(gri)

        
        if len(yuzler) == 1:
            x, y, w, h = yuzler[0]
            cv2.rectangle(kare, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if time.time() - son_kayit > 0.3:  
                yuz = yuzu_hazirla(gri, yuzler[0])
                kaydedilen += 1
                resim_kaydet(kisi_klasoru / f"{mevcut + kaydedilen:03d}.jpg", yuz)
                son_kayit = time.time()

        bilgi = f"{ascii_yap(isim)}: {kaydedilen}/{config.FOTO_SAYISI}  (cikis: q veya ESC)"
        cv2.putText(kare, bilgi, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow(PENCERE, kare)
        if cikis_istendi(PENCERE):
            break

    kamera.release()
    cv2.destroyAllWindows()
    return kaydedilen
