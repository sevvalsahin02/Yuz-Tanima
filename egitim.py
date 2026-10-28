
import json
import cv2
import numpy as np
import config
from yardimci import resim_oku, model_kaydet


def tanimlayici_olustur():
    
    if config.ALGORITMA == "fisher":
        return cv2.face.FisherFaceRecognizer_create()
    return cv2.face.LBPHFaceRecognizer_create()


def egit() -> str:
    
    resimler, etiketler, isimler = [], [], []

    kisi_klasorleri = sorted(k for k in config.VERI_KLASORU.iterdir() if k.is_dir())
    for klasor in kisi_klasorleri:
        dosyalar = list(klasor.glob("*.jpg"))
        if not dosyalar:
            continue
        etiket = len(isimler)          
        isimler.append(klasor.name)
        for dosya in dosyalar:
            resim = resim_oku(dosya)
            if resim is None:
                continue
            resimler.append(cv2.resize(resim, config.YUZ_BOYUTU))
            etiketler.append(etiket)

    if not isimler:
        return "Hiç fotoğraf yok. Önce 'Yüz Ekle' ile veri toplayın."
    if config.ALGORITMA == "fisher" and len(isimler) < 2:
        return "Fisherface için en az 2 kişi gerekir. Bir kişi daha ekleyin ya da config.py'de ALGORITMA = 'lbph' yapın."

    tanimlayici = tanimlayici_olustur()
    tanimlayici.train(resimler, np.array(etiketler))

    config.MODEL_YOLU.parent.mkdir(exist_ok=True)
    model_kaydet(tanimlayici, config.MODEL_YOLU)
    with open(config.ETIKET_YOLU, "w", encoding="utf-8") as f:
        json.dump(isimler, f, ensure_ascii=False)

    return f"Eğitim tamam: {len(isimler)} kişi, {len(resimler)} fotoğraf. ({', '.join(isimler)})"
