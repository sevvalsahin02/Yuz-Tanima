from pathlib import Path

KOK = Path(__file__).resolve().parent
VERI_KLASORU = KOK / "veri" / "yuzler"        
MODEL_YOLU = KOK / "model" / "yuz_modeli.xml"  
ETIKET_YOLU = KOK / "model" / "etiketler.json"  
CASCADE_YOLU = KOK / "cascade" / "haarcascade_frontalface_default.xml"  

KAMERA_NO = 0           
YUZ_BOYUTU = (100, 100)  
FOTO_SAYISI = 60         
ALGORITMA = "lbph"

ESIK = {"lbph": 110, "fisher": 1500}   # kendi sayılarına göre ayarla
