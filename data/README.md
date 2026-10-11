# data klasörü

Bu klasör otomasyonun çalışma anı verilerini (checkpoint, log özeti, canlı adımlar) tutar.

## Personel Excel dosyası (özel/hassas)

Yolluk otomasyonu personel listesini şu dosyadan okur:

    data\Yolluk Liste 7.xlsx

- Dosya henüz bu makineye kopyalanmadıysa otomasyon şu anlaşılır hata verir:
  "Excel dosyası bulunamadı ..." (çıplak traceback değil).
- Dosya adı farklıysa `config/runner-settings.json` içindeki `sourceWorkbook`
  değerini güncelleyin (göreli yol proje köküne göre çözülür; mutlak yol da yazabilirsiniz).
- Bu dosya TCKN/IBAN gibi hassas veri içerir. `.gitignore` gereği (*.xlsx)
  ASLA git'e eklenmez.

Excel yapısı:
- 1. sayfa: personel listesi (TC NO, AD, SOYAD, UNVAN, DERECE, KADEME, EK GÖSTERGE,
  GÜNDELİĞİ, GEÇ. GÖREV TARİHİ, GÜN SAYISI, IBAN).
- 2. sayfa: Birim Amiri TCKN'si (TC/TCKN etiketinin sağındaki 11 haneli değer).
