# MYS-YOLLUK-OTOMASYON

MYS "Yolluk Süreç Hazırlama" formunu Excel'den otomatik dolduran yerel otomasyon
(Aşama 1). Canlı gönderim varsayılan olarak kilitlidir.

## ÖNCE OKU

**[PROJECT_KNOWLEDGE_TREE.md](PROJECT_KNOWLEDGE_TREE.md)** — Projenin hafızası:
kodlama kuralları, dosya haritası, ana akış, güvenlik ilkeleri ve değişiklik günlüğü.
Kod değiştirmeden önce bu dosyayı oku.

Ek kaynaklar:
- `README-STAGE1.txt` — Aşama 1 akışı ve güvenli çalışma kuralları.
- `PROJECT_HANDOFF_AI.md` — Detaylı devir/tanı dokümanı (MYS alanları, Excel yapısı).
- `PROJECT_KNOWLEDGE_TREE.md` — Güncel durum + kodlama kuralı + changelog.

## Hızlı başlangıç

```powershell
python scripts\yolluk-controller.py     # Panel -> http://127.0.0.1:8765
python scripts\stage1-live-run.py --stop-before-submit   # Güvenli dry-run
python tests\test-assignment.py         # Birim testler
python tests\test-playwright-connection.py # Playwright bağlantı başlatma testleri
python tests\test-workbook-support.py   # Excel şablonu/yükleme doğrulama testi
python tests\test-workbook-panel.py     # Panelin yerel yükleme/şablon uçları
```

Paneli `scripts\yolluk-panel.bat` ile başlatabilirsiniz. BAT, eski panel bu projeye
aitse ve otomasyon çalışmıyorsa onu güvenle kapatıp güncel paneli yeniden açar;
işlem sürerken veya portu başka bir uygulama kullanırken kapatma yapmaz.

Kontrol panelindeki **Excel dosyası** bölümünden `.xlsx` dosyası yükleyebilir veya
boş şablonu indirebilirsiniz. Şablonun ilk sayfasına personel satırlarını, ikinci
sayfasında `TC/TCKN` etiketinin hemen sağına Birim Amiri TCKN'sini girin. Yüklenen
dosya paneldeki sonraki işlemlerde seçilen dosya yolu/ismi değişse bile kullanılır;
Excel dosyaları yerel tutulur ve Git'e eklenmez.

Otomasyon başlangıcında `chrome-main` ve Chrome'daki yeşil Playwright grubu kontrol
edilir. `autoStartPlaywrightConnection` açıkken bağlantı hazır değilse proje içindeki
Playwright bağlantı BAT'ı bir kez başlatılır; hazır bağlantıda yeni Allow & select
ekranı açılmaz. Chrome uzantısındaki izin/seçim ve MYS oturum açma adımlarını kullanıcı
tamamlar. Bu seçenek `config/runner-settings.json` üzerinden kapatılabilir.
Bağlantı guard'ı, mevcut kuralla uyumlu olarak diğer bağlı Playwright oturumlarını
detach edebilir; Chrome pencerelerini kapatmaz. Aynı adlı session çakışmasında güvenli
biçimde bekler.
