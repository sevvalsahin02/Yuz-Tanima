
import shutil
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

import config
from egitim import egit
from tanima import tani
from veri_toplama import veri_topla


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class Uygulama(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Yüz Tanıma")
        self.geometry("380x560")
        self.resizable(False, False)

        
        ctk.CTkLabel(
            self,
            text="Yüz Tanıma Sistemi",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 10))

       
        kart1 = ctk.CTkFrame(self, corner_radius=10)
        kart1.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(kart1, text="1) Kişinin adı:", font=ctk.CTkFont(weight="bold")).pack(pady=(8, 2))
        self.isim_kutusu = ctk.CTkEntry(kart1, width=260, placeholder_text="İsim giriniz...")
        self.isim_kutusu.pack(pady=4)

        ctk.CTkButton(
            kart1,
            text="📷 Yüz Ekle (kameradan foto çek)",
            width=260,
            command=self.yuz_ekle
        ).pack(pady=(4, 10))

        
        kart_yonetim = ctk.CTkFrame(self, corner_radius=10)
        kart_yonetim.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(kart_yonetim, text="Kayıtlı Kişiler:", font=ctk.CTkFont(weight="bold")).pack(pady=(8, 2))
        self.kisi_secim = ctk.CTkOptionMenu(kart_yonetim, values=["Kayıtlı kişi yok"], width=260)
        self.kisi_secim.pack(pady=4)

        ctk.CTkButton(
            kart_yonetim,
            text="🗑️ Seçili Kişiyi Sil",
            fg_color="#DC2626",
            hover_color="#991B1B",
            width=260,
            command=self.kisi_sil
        ).pack(pady=(4, 10))

        
        kart2 = ctk.CTkFrame(self, corner_radius=10)
        kart2.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(kart2, text="2) Yeterince kişi eklenince:").pack(pady=(8, 2))
        ctk.CTkButton(
            kart2,
            text="⚙️️ Modeli Eğit",
            fg_color="#D97706",
            hover_color="#B45309",
            width=260,
            command=self.model_egit
        ).pack(pady=(4, 10))

        
        kart3 = ctk.CTkFrame(self, corner_radius=10)
        kart3.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(kart3, text="3) Tanıma:").pack(pady=(8, 2))
        ctk.CTkButton(
            kart3,
            text="🚀 Yüz Tanımayı Başlat",
            fg_color="#059669",
            hover_color="#047857",
            width=260,
            command=self.tanimayi_baslat
        ).pack(pady=(4, 10))

        
        self.durum = ctk.CTkLabel(self, text="Hazır", text_color="gray")
        self.durum.pack(side="bottom", pady=12)

        self.kisileri_guncelle()

    def kisileri_guncelle(self):
        yuzler_yolu = Path(config.VERI_KLASORU)
        if not yuzler_yolu.exists():
            yuzler_yolu.mkdir(parents=True, exist_ok=True)

        kisiler = [f.name for f in yuzler_yolu.iterdir() if f.is_dir()]
        if kisiler:
            self.kisi_secim.configure(values=kisiler)
            self.kisi_secim.set(kisiler[0])
        else:
            self.kisi_secim.configure(values=["Kayıtlı kişi yok"])
            self.kisi_secim.set("Kayıtlı kişi yok")

    def kisi_sil(self):
        secilen = self.kisi_secim.get()
        if secilen == "Kayıtlı kişi yok" or not secilen:
            messagebox.showwarning("Uyarı", "Silinecek kişi seçilmedi.")
            return

        if messagebox.askyesno("Onay", f"'{secilen}' kişisini silmek istiyor musunuz?"):
            hedef = Path(config.VERI_KLASORU) / secilen
            if hedef.exists():
                shutil.rmtree(hedef)
                self.kisileri_guncelle()
                messagebox.showinfo("Başarılı", f"'{secilen}' silindi. Modeli tekrar eğitin!")

    def yuz_ekle(self):
        isim = self.isim_kutusu.get().strip()
        if not isim:
            messagebox.showwarning("Uyarı", "Önce bir isim yazın.")
            return
        self.durum.configure(text="Kamera açık... (çıkmak için q)")
        self.update()
        try:
            sayi = veri_topla(isim)
            self.durum.configure(text=f"{isim}: {sayi} fotoğraf kaydedildi")
            self.isim_kutusu.delete(0, "end")
            self.kisileri_guncelle()
        except Exception as hata:
            messagebox.showerror("Hata", str(hata))
            self.durum.configure(text="Hata oluştu")

    def model_egit(self):
        self.durum.configure(text="Eğitiliyor...")
        self.update()
        try:
            mesaj = egit()
        except Exception as hata:
            mesaj = f"Hata: {hata}"
        self.durum.configure(text="Hazır")
        messagebox.showinfo("Eğitim", mesaj)

    def tanimayi_baslat(self):
        try:
            tani()
        except Exception as hata:
            messagebox.showerror("Hata", str(hata))


if __name__ == "__main__":
    config.VERI_KLASORU.mkdir(parents=True, exist_ok=True)
    Uygulama().mainloop()