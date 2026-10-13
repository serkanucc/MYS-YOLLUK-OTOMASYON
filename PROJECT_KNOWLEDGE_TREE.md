# MYS YOLLUK OTOMASYONU — PROJE BİLGİ AĞACI / AI EL KİTABI

> BU DOSYA PROJENİN HAFIZASIDIR. Kod değiştirmeden önce MUTLAKA oku.
> Kodlama kuralı, mimari, güvenlik ilkeleri ve tüm değişiklik günlüğü burada tutulur.
> Son güncelleme: 2026-10-12

---

## 0. KODLAMA KURALI — ZORUNLU (kullanıcı talimatı)

**Her kod değişikliğinde/düzeltmede/eklemede:**
1. Değiştirilen/eklenen her mantıklı kod bloğunun başına kısa yorum yaz:
   - *Neden* yapıldı (hangi hatayı/bug'ı çözüyor), *ne işe yarıyor*.
   - Örnek: `# Bozuk satırı atla, tüm listeyi çökertme (tek hatalı tarih tüm işi durduruyordu).`
2. Aşağıdaki DEĞİŞİKLİK GÜNLÜĞÜ'ne satır ekle: tarih, dosya, ne, neden, etki.
3. Hassas veri (TCKN/IBAN/şifre) ASLA kod/log/git'e yazılmaz.
4. Değişiklik sonrası ilgili testleri çalıştır (`python tests/...`).

Bu kural kullanıcı tarafından istenmiştir ve bağlayıcıdır.

---

## 1. PROJE NE YAPAR?

Sağlık Bakanlığı MYS sistemindeki "Yolluk Süreç Hazırlama" formunu Excel personel
listesinden otomatik doldurur, mükerrer kayıt kontrolü yapar ve CANLI GÖNDERİMİ
VARSAYILAN OLARAK KİLİTLİ tutar. Gerçek Chrome oturumu üzerinden (Playwright CLI).

```
Excel → stage1-live-run.py (motor) → playwright-cli -s=chrome-main → Chrome → MYS
              ↑
 yolluk-controller.py (panel :8765)  +  assistant-stage1.py (sohbet girişi)
```

---

## 2. DOSYA HARİTASI (hangi dosya ne işe yarar)

### scripts/
| Dosya | Rol | Durum |
|---|---|---|
| `stage1-live-run.py` | **Ana motor.** Excel okur, IBAN/tarih doğrular, mükerrer kontrol, formu doldurur, güvenli submit veya submit butonuna basmayan test simülasyonu. | ✅ Aktif |
| `assignment.py` | **Saf mantık.** Tarih çözümleme (`duty_period`), görev kimliği (`assignment_id`), çakışma sınıflandırma (`classify_candidates`). Testli. | ✅ Aktif |
| `yolluk-controller.py` | **Kontrol paneli** (http://127.0.0.1:8765). Durum, canlı adımlar, log, başlat/durdur. | ✅ Aktif |
| `yolluk-panel.bat` | Paneli başlatır (port açıksa sadece tarayıcı açar). | ✅ Aktif |
| `playwright_connection.py` | Playwright CLI yolunu çözer, yeşil Chrome grubunu doğrular ve gerektiğinde proje içi bağlantı BAT'ını başlatır. | ✅ Aktif |
| `playwright-connection/` | Kullanıcının Chrome Allow & select bağlantı akışının projeye taşınmış guard/BAT dosyaları. | ✅ Aktif |
| `stage1-flow-pre.js` | Formun ilk yarısı (TCKN, Mernis, maaş, IBAN). `needsIbanCommit` döner. | ✅ Aktif |
| `stage1-flow-post.js` | Formun ikinci yarısı (tarih, kaynak/program/faaliyet, bütçe tertibi, Birim Amiri). `submitDisabled` döner. | ✅ Aktif |
| `stage1-flow.js` | pre+post birleşik hali (eski tek parça). `make_iban_flows.py` ile üretilir. | ⚠️ Referans |
| `duplicate-check.js` | MYS sorgu sayfasında TCKN ile "Sorgula" yapar, satırları çeker. | ✅ Aktif |
| `excel-read.py` | Excel'i basit JSON okur (tanılama/yardımcı). | ⚠️ Yardımcı |
| `stage1-flow-run.py` | Eski tek-seferlik form akışı (PW-GREEN-CHECK kullanır). Motor bunu KULLANMAZ. | ⚠️ Legacy |
| `duplicate-check-run.py` | Sadece mükerrer sorgu (ilk satırın TCKN'i ile). | ⚠️ Yardımcı |
| `make_test_excel.py` | **Test amaçlı SAHTE Excel üretir** (MOD-97 geçerli ama gerçek-olmayan IBAN). | ✅ Test |
| `make_iban_flows.py` | `stage1-flow.js` → `stage1-flow-pre.js` + `stage1-flow-post.js` üretir. | ⚠️ Tek seferlik |
| `assistant-stage1.py` | Sohbet/GPT girişi. `session-manifest.json` yazıp motoru çağırır. | ⚠️ Orkestrasyon |

### config/
| Dosya | Rol |
|---|---|
| `runner-settings.json` | **Ana ayar.** URL'ler, `browserSession`, `sourceWorkbook` (göreli), güvenlik kilitleri. |
| `fixed-values.json` | Form sabit değerleri (yolluk tipi, program, bütçe tertibi vb.). |
| `excel-map.json` | Excel alan eşlemesi — **DOKÜMAN, koddan okunmuyor**. |
| `stage1-fields.json` | Form alan etiketleri — **DOKÜMAN, koddan okunmuyor**. |
| `stage1-status.json` | Durum kodları açıklaması — **DOKÜMAN, koddan okunmuyor**. |
| `stage1-rules.md` | Derece/kademe/gündelik kuralları. |

### data/
| Dosya | Rol |
|---|---|
| `checkpoint.json` | Görev bazlı devam durumu (git'te izlenir). |
| `live-steps.json` | Panelde canlı adımlar (git'ten hariç). |
| `session-manifest.json` | Sohbet kontrollü çalışma manifesti. |
| `Yolluk Liste 7.xlsx` | **Gerçek personel verisi — GIT'E ASLA EKLENMEZ** (`*.xlsx` ignore). |
| `mys-main.js`, `rt-source.txt`, `guide-index.html` | MYS arayüz ters-mühendislik referansları (vendor). |

### tests/
| Dosya | Rol |
|---|---|
| `test-assignment.py` | Tarih biçimleri, dahilî gün sayısı doğrulaması, `assignment_id` + `classify_candidates` (EXACT/OVERLAP). |
| `test-read-amir.py` | `read_amir_tckn` (2. sayfa, TCKN temizliği). |
| `test-stage1-runner-policy.py` | Gerçek tamamlanan kaydı atlama ve simülasyonun tekrar çalışabilmesi. |

---

## 3. ANA AKIŞ (stage1-live-run.py main → tamamlanma)

1. CLI çözümleme (`resolve_cli`): config → PATH → %APPDATA%. Yoksa None.
2. Bağlantı kontrolü (`wait_for_playwright`): CLI_MISSING ise HATA, değilse OK bekle.
3. Excel okuma (`people`): dosya yoksa net hata; SATIR BAZLI HATA DAYANIKLI
   (bozuk satırı atla+logla, `EXCEL_ROW_SKIPPED`).
4. Her personel için: STAGE1_COMPLETED ise atla → save(PROCESSING) →
   `duplicate(x)` (tek Sorgula; aynı sonuç tarih kontrolü ve baseline_ids için kullanılır)
   → `classify_candidates` (EXACT/OVERLAP/AMBIGUOUS, yalnız tarih çakışmasında bilgi
   verir ama ENGEL DEĞİL) → form doldur (js_pre → IBAN Enter →
   js_post, 2 deneme) → READY_TO_SUBMIT → `--simulate-submit` ise TEST- numara yaz
   ve sonuç Excel'i üret (MYS submit tıklanmaz) → canlı değilse dur → güvenlik kilidi →
   canlıysa tek tık → SUBMITTING → SUBMITTED_UNVERIFIED → STAGE1_COMPLETED
   (doğrulama: baseline ID + tam tarih, sıraya GÜVENME).

---

## 4. GÜVENLİK İLKELERİ (DEĞİŞTİRME)

- Canlı gönderim ÇİFT KİLİTLİ: liveSubmissionEnabled=false + --stop-before-submit.
- Canlı modda submit butonuna TEK TIK; ikinci tık yasak; belirsizlikte yeniden tıklama YOK.
- `--simulate-submit` gerçek MYS kaydı oluşturmaz; TEST- önekli numara kullanır.
- Sonuç dosyası kaynak Excel'in kopyasıdır; `data\Yolluk Sonuc.xlsx` olarak üretilir.
- Sonuç Excel'i panel oturumunda üretilmiş başarılı simülasyondan sonra sunulur; panel açılışında veya yeni Excel yüklemesinde önceki sonuç geçersiz kılınır.
- Kayıt doğrulama: sıraya değil BASELINE ID'lerden ayrışmış yeni kayıt + tam tarih eşleşmesi.
- Otomasyon ASLA MYS girişi yapmaz; oturum düşerse kullanıcıdan bekler (ensure_mys_session).
- E-imza/2FA/CAPTCHA bypass EDİLMEZ.
- Ana sayfa listesi her okumada MUTLAKA Sorgula ile tazelenir (güvenilir liste yoktur).
- Excel (TCKN/IBAN) ASLA git'e/log'a yazılmaz.

## 5. TAŞINABİLİRLİK (makine/kullanıcı değişse de çalışsın)

- Kullanıcı/makine yolu KODA GÖMÜLMEZ. playwright-cli yolu resolve_cli() ile
  çalışma anında bulunur (config cliPath -> shutil.which -> %APPDATA%\npm).
- Excel yolu GÖRELİ (data\Yolluk Liste 7.xlsx), proje köküne göre çözülür.
  Mutlak yol da yazılabilir (Path.is_absolute() kontrolü var).
- --excel <dosya> ile geçici yol verilebilir.

## 6. DURUM KODLARI

PROCESSING, READY_TO_SUBMIT, SUBMITTING, SUBMITTED_UNVERIFIED, STAGE1_COMPLETED,
ERROR, DUPLICATE_WARNING_CONTINUING, AMBIGUOUS_DUPLICATE, USER_INFORMATION_REQUIRED,
STOP_BEFORE_SUBMIT (test modu). Açıklama: config/stage1-status.json.

## 7. ÇALIŞTIRMA

```powershell
python scripts\yolluk-controller.py       # Panel -> http://127.0.0.1:8765
python scripts\make_test_excel.py         # Sahte test verisi üret
python scripts\stage1-live-run.py --stop-before-submit   # Güvenli dry-run (kayıt yok)
python scripts\stage1-live-run.py --simulate-submit      # Test: gerçek kayıt yok, sahte no + sonuç Excel'i
python tests\test-assignment.py           # ASSIGNMENT TESTS OK
python tests\test-read-amir.py            # READ_AMIR_TCKN TESTS OK

### 2026-10-11 (akşam) — Geçersiz TCKN'de "Mernis personel bulunamadı" durum tespiti
Amaç: Gerçek-olmayan/geçersiz TCKN'de otomasyonun "Birim Amiri TCKN alanı bulunamadı"
hatasıyla ÇÖKMESİNİ engelle. Kullanıcı bulgusu: Mernis sadece geçerli/gerçek TCKN'de
personel döndürür; geçersizse Ad Soyad/IBAN/Birim Amiri alanları DOM'da hiç oluşmaz.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 7 | stage1-flow-pre.js | Mernis/Maaş sonrası Ad Soyad alanının dolup dolmadığını kontrol et; boşsa personelBulunamadi döndür. | MANTIK: geçersiz TCKN'de personel gelmez, IBAN alanı da olmaz. Artık çökmez, durumu bildirir. |
| 8 | stage1-flow-post.js | birimAmiriTcknInput yoksa hata fırlatmak yerine personelBulunamadi döndür. | MANTIK: alan yokluğu geçersiz TCKN'nin işareti; hata değil durum. |
| 9 | stage1-live-run.py | pre ve post sonuçlarında personelBulunamadi kontrolü; USER_INFORMATION_REQUIRED kaydet, submit'a geçmeden sonraki kişiye geç. | GÜVENLİ AKIŞ: tahmin yok, boş form doldurmaya çalışmaz, kullanıcıya net mesaj. |


## 8. DEĞİŞİKLİK GÜNLÜĞÜ (CHANGELOG) — en yenisi üstte

### 2026-10-12 — Excel görev tarihi ve gün sayısı kuralı
Amaç: Kısa tarih biçimlerini açık bir kurala bağla ve Excel'deki gün sayısı
tarihlerin ürettiği görev günleriyle çelişirse yanlış satırı işleme.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/assignment.py, scripts/stage1-live-run.py | Aynı ay gün listesi ve iki ucu dahil gün aralığı sayılır; `GÜN SAYISI` pozitif tam sayı ve hesapla aynı olmalı. | Tarih aralığı ile bildirilen gün adedi uyuşmazsa satır loglanıp atlanır. |
| 2 | scripts/workbook_support.py | Excel yükleme doğrulamasında `GÜN SAYISI` başlığı zorunlu. | Panelden yüklenen şablonun zorunlu alanı eksikse erken uyarı verir. |
| 3 | tests/test-assignment.py | Noktalı kısa liste, dahilî aralık, doğru/yanlış/boş gün sayısı senaryoları eklendi. | Kullanıcıyla kararlaştırılan tarih kuralını korur. |
| 4 | README.md | Tercih edilen kısa tarih yazımları ve 03–13 örneğinin 11 gün olduğu belgelendi. | Excel'e veri giriş biçimi netleşir. |

### 2026-10-12 — Önceki simülasyonun yeni testi atlamasını önleme
Amaç: Kuru test ve form doldurma düğmeleri önceki SIMULATED_COMPLETED checkpoint'inde
işlemi atlayıp yalnız RUN_COMPLETE yazmasın; simülasyon gerçek MYS kaydı oluşturmaz.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/stage1-live-run.py | Atlanan işler politikası yalnız gerçek STAGE1_COMPLETED kayıtlarını varsayılan olarak atlar. | Önceki sahte sonuç yeni kuru test/form doldurmayı engellemez. |
| 2 | tests/test-stage1-runner-policy.py | Gerçek tamamlanmış işin atlanması ve simülasyonun tekrar denenmesi doğrulanır. | Checkpoint tekrar çalıştırma davranışı regresyona karşı korunur. |
| 3 | README.md, PROJECT_KNOWLEDGE_TREE.md | Simülasyon tekrar çalıştırılabilir olarak belgelenir. | Kullanıcı eski simülasyonun yeni testi engellemediğini bilir. |

### 2026-10-12 — Eski sonuç Excel'ini yeniden sunmayı engelleme
Amaç: Panel yeniden açıldığında veya başka bir Excel yüklendiğinde önceki çalıştırmanın
sonucunun yeni sonuç gibi indirilebilmesini önle.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/yolluk-controller.py | Açılışta ve yeni iş/yüklemede eski sonuç temizlenir; indirme yalnız panel oturumunda başarıyla tamamlanan simülasyon için açılır. | Önceki oturumun dosyası tekrar sunulmaz; başarısız/çalışan simülasyon indirmeye kapalıdır. |
| 2 | tests/test-workbook-panel.py | Eski dosya, devam eden simülasyon ve tamamlanmış simülasyon indirmesi doğrulanır. | Sonuç Excel'i oturum sahipliği ve bitiş durumuna göre test edilir. |
| 3 | README.md, PROJECT_KNOWLEDGE_TREE.md | Sonuç dosyasının oturum-geçerliliği belgelenir. | Kullanıcının sonuç dosyası davranışı açıktır. |

### 2026-10-12 — Yolluk Liste 7 ile uyumlu örnek şablon başlıkları
Amaç: İndirilen boş şablonda kullanılan kurum ve geçici görev kurum sütunlarının
eksik olmasını gider; kaynak listedeki başlıkları kişisel veri kopyalamadan koru.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/workbook_support.py | `GELDİĞİ KURUM`, `GEÇ. GÖREV ÇALIŞTIĞI KURUM` ve `Yolluk Tutar` kaynak başlıkları eklendi; `YOLLUK NO` son sütun olarak bırakıldı. | Boş şablon Yolluk Liste 7 ile aynı kolon düzenini sunar. |
| 2 | tests/test-workbook-support.py | Tüm örnek şablon başlık sırası ve kişisel veri içermeyen tek başlık satırı doğrulanır. | Şablon düzeninin gerilemesini önler. |
| 3 | README.md | Şablonun kurum alanları dahil kaynak listedeki başlıkları koruduğu belirtildi. | Kullanıcı şablon içeriğini önceden görür. |

### 2026-10-12 — Son adım simülasyonu ve sonuç Excel'i
Amaç: MYS'de gerçek kayıt oluşturmadan son gönderim adımını uçtan uca test et ve
üretilen sahte yolluk numarasını kullanıcıya indirilebilir Excel'de göster.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/workbook_support.py | Boş şablona son `YOLLUK NO` sütunu eklendi; kaynak kopyasında satıra TEST- numarası yazma ve benzersiz numara üretme işlevleri eklendi. | Kaynak Excel değişmeden sonuç dosyası indirilebilir. |
| 2 | scripts/stage1-live-run.py | `--simulate-submit` form hazırken MYS butonuna basmaz; sahte numara üretir, Excel satırına ve checkpoint'e yazar. | Son adımın güvenli testini sağlar; canlı kilitleri değiştirmez. |
| 3 | scripts/yolluk-controller.py | Panelde simülasyon düğmesi ve sonuç Excel indirme endpoint'i/bağlantısı eklendi. | Test sonucu panelden indirilebilir. |
| 4 | tests/test-workbook-support.py, tests/test-workbook-panel.py | Şablon başlığı, kopya koruması, sahte numara yazımı ve indirme endpoint'i test edildi. | Excel çıktı akışını doğrular. |
| 5 | README.md | Simülasyon ve sonuç indirme akışı belgelendi. | Gerçek submit yapılmadığı açıkça belirtilir. |

### 2026-10-12 — Mükerrer sorguda yalnız tarih çakışması uyarısı
Amaç: Başka tarihlerdeki geçmiş yolluk kayıtlarını sessizce atla; yalnız aynı/kesişen görev tarihlerini bilgi amaçlı göster ve işleme devam et.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/stage1-live-run.py | Duplicate sonuçlarından yalnız kesin EXACT/OVERLAP aralıkları seçilir; uyarı metni çakışan tarihleri açıkça listeler. AMBIGUOUS ve farklı tarihli kayıtlar uyarı üretmez. | Kullanıcı yalnız istenen tarih çakışmasında bilgilendirilir; işlem hata sayılmaz ve durmaz. |
| 2 | tests/test-assignment.py | Farklı tarihin sessiz kalması ve belirsiz kaydın uyarı listesinden çıkarılması testleri eklendi. | Tarih çakışması bildirim kapsamını korur. |

### 2026-10-12 — Playwright bağlantısını otomatik başlatma
Amaç: Kullanıcı bağlantı BAT'ını elle çalıştırmadan önce `chrome-main` ve Chrome yeşil grubunu denetle; eksik bağlantıda mevcut Allow & select akışını başlat.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | config/runner-settings.json | `autoStartPlaywrightConnection` ayarı eklendi (varsayılan açık). | İstenirse otomatik başlatma kapatılabilir. |
| 2 | scripts/playwright_connection.py | CLI JS çözümleme, yeşil grup kontrolü ve proje içi BAT başlatma işlevleri eklendi. | Kullanıcı klasörüne sabit yol koymadan bağlantı akışını kullanır. |
| 3 | scripts/playwright-connection/ | Kullanıcının BAT/PowerShell guard akışı proje içine taşındı; sabit kullanıcı yolu kaldırılıp npm/APPDATA üzerinden çözülüyor. | Aynı bağlantı davranışını proje içinden çalıştırır; sağlıklı oturumda yeni attach açmaz. |
| 4 | scripts/stage1-live-run.py | Sağlık kontrolü yeşil Chrome grubunu da şart koşar; eksik bağlantıda yardımcı BAT bir kez başlatılır ve kullanıcı onayı beklenir. | Attach var ama kullanıcı Allow & select yapmamışsa otomasyon erken ilerlemez. |
| 5 | tests/test-playwright-connection.py | CLI yolu, yardımcı BAT çağrısı ve sağlıklı/eksik bağlantıda başlatma davranışı test edildi. | Otomatik bağlantı başlatıcısının taşınabilirliğini ve hazır bağlantıyı çoğaltmamasını doğrular. |
| 6 | README.md | Otomatik bağlantı davranışı, kullanıcı adımları ve diğer session'ları detach edebilmesi belgelendi. | Beklenen izin adımları ve guard yan etkisi açıklanır. |

### 2026-10-12 — Çalışma ortasında yeniden attach'i engelleme
Amaç: Form doldurma sırasında yeşil grup kontrolünün geçici başarısızlığıyla bağlantı BAT'ının yeniden açılmasını önle.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/stage1-live-run.py | Yeşil grup ve otomatik başlatma yalnız otomasyon başlangıcında çalışır; sonraki Playwright komutları mevcut CLI attach'i bekler ve yeni attach başlatmaz. | Form akışı ortasında gereksiz Allow & select/reattach oluşmaz; bağlantı koparsa kullanıcı bağlantıyı düzeltince akış sürer. |
| 2 | tests/test-playwright-connection.py | Başlangıçta bir kez başlatma, hazır bağlantıda başlatmama ve işlem sırasında başlatmama durumları test edildi. | İstenmeyen ara bağlantı başlatmasının regresyonunu engeller. |

### 2026-10-12 — Submit öncesi MYS sorgusunu tekilleştirme
Amaç: Aynı kişi için tarih çakışması ve baseline kayıt ID'leri amacıyla yapılan yinelenen Sorgula işlemini tek sorguda birleştir.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/stage1-live-run.py | Duplicate kontrolündeki taze sorgu sonucu baseline ID toplamada yeniden kullanılıyor; ikinci pre-submit sorgu kaldırıldı. `--skip-duplicate` verilirse baseline için tek sorgu yapılır. | Normal akışta form açılmadan önce aynı TCKN için iki Sorgula yerine bir Sorgula yapılır; submit sonrası doğrulama sorgusu aynen korunur. |

### 2026-10-12 — Panel BAT güvenli yeniden başlatma
Amaç: BAT ile açılan panel eski kodu bellekte tutup yeni Excel ekranını göstermeme sorununu çöz.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/yolluk-panel.bat | Önce güvenli panel yenileme betiği çağrılıyor; ardından proje sanal ortamı tercih edilerek sunucu açılıyor ve hazır olunca tarayıcı açılıyor. | Var olan panel sürecinde eski HTML görünmesini önler; eksik/başarısız başlatmayı ekranda bildirir. |
| 2 | scripts/restart-panel.ps1 | Yalnızca doğrulanmış Python panel PID'si ve otomasyon boşta ise `Stop-Process -Id` ile kapatılır; port sahibi belirsizse veya iş sürüyorsa kapatma reddedilir. | Başka uygulamayı veya devam eden MYS otomasyonunu yanlışlıkla durdurmayı önler. |
| 3 | README.md | BAT başlatıcısının güvenli yenileme davranışı belgelendi. | Çalışma sürerken paneli kapatmanın neden engellendiğini açıklar. |

### 2026-10-12 — Panelden Excel yükleme ve boş şablon
Amaç: Dosya adı/konumu değişse de kullanıcıya panelden Excel seçip yükleme ve doğru kolonlu boş şablon indirme imkânı ver.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | scripts/workbook_support.py | Motorun beklediği sütun/sayfa yapısını doğrulama ve boş Excel şablonu üretme işlevleri eklendi. | Yanlış veya okunamayan dosyanın seçilmesini önler; gerçek personel verisi içermeyen başlangıç şablonu sağlar. |
| 2 | scripts/yolluk-controller.py | Yerel panele `.xlsx` yükleme endpoint'i ve şablon indirme endpoint'i eklendi; yüklenen çalışma kitabı başlatma sırasında motora aktarılır. | Excel yolu/adı değişikliklerinden bağımsız kullanım sağlar. Yükleme 20 MB ile sınırlı ve otomasyon çalışırken kilitlidir. |
| 3 | tests/test-workbook-support.py | Boş şablonun yükleme doğrulamasından geçtiği ve hatalı başlıkların reddedildiği test edildi. | Şablon ve upload yapısının motorla uyumunu regresyona karşı korur. |
| 4 | tests/test-workbook-panel.py | Yerel HTTP endpoint'lerinden şablon indirme/yükleme ve yabancı Origin reddi doğrulandı. | Panelin upload/download yollarını uçtan uca test eder. |
| 5 | README.md | Panelde Excel yükleme ve şablon kullanımı belgelendi. | Kullanıcıya yeni özelliğin kullanım adımlarını açıklar. |

### 2026-10-12 — Yerel runtime Excel ayarını kullanma
Amaç: Ana motorun makineye özel Excel yolunu yok sayıp mevcut olmayan varsayılan dosyada hata vermesini düzelt.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | stage1-live-run.py | `runner-settings.runtime.json` içindeki `sourceWorkbook` önce deneniyor; dosya yoksa ana config yoluna dönülüyor. Eksik dosya hatası artık kontrol edilen tüm yolları gösteriyor. | Runtime ayarında mevcut Excel dosyası tanımlı olmasına rağmen motor yalnızca taşınabilir varsayılan yolu kullanıyordu. Makineye özel yol uygulanır, varsayılan taşınabilirlik korunur. |

### 2026-10-11 — Kapsamlı hata avı + taşınabilirlik + bilgi ağacı
Amaç: Projeyi uçtan uca incele, kod/mantık hatalarını bul ve düzelt, kalıcı hafız kur.

| # | Dosya | Değişiklik | Neden / Etki |
|---|---|---|---|
| 1 | assignment.py | classify_candidates artık `DATES:` alanı varsa SADECE ona güveniyor (satırdaki yabancı tarihleri değil). | MANTIK HATASI: MYS liste satırındaki oluşturma tarihi vb. aralığı bozuyordu (01/01/2025..10/08/2026 gibi saçma aralık). Artık doğru çakışma sınıflanıyor. |
| 2 | assignment.py | parse_duty_dates: ters/ay-sınırı aralığı (31-01) açık hata; ay gün sayısını aşan aralık (_range_days) hata. | MANTIK HATASI: sorted()+range() sessizce yanlış aralık üretiyordu (31-01/12 -> 31 gün). Artık kullanıcı netleştirsin. |
| 3 | stage1-live-run.py | people() SATIR BAZLI hata dayanıklı (try/except); bozuk satırı atla+logla. GÜN SAYISI indeksi bir kez hesaplanıyor. | MANTIK HATASI: tek bozuk tarih/IBAN tüm Excel işlemini çökertiyordu. Artık sağlıklı satırlar işlenir (EXCEL_ROW_SKIPPED logu). |
| 4 | stage1-live-run.py | "\\nDATES:" -> "\nDATES:". | KAÇIŞ HATASI: literal \n metni, gerçek satır sonu değildi; DATES: mekanizması hiç çalışmıyordu. |
| 5 | stage1-live-run.py | datetime import'u kaldırıldı. | Kod hijyeni (kullanılmayan import). |
| 6 | stage1-live-run.py | restart_test.py ve patch_history.py SİLİNDİ. | GÜVENLİK: restart_test.py taskkill /F /IM python.exe ile TÜM python süreçlerini öldürüyordu; ikisi de eski serkan.suc yoluna sabitli ölü/tehlikeli script. |

### 2026-10-11 — Oturum düşme tespiti (önceki adım)
- is_login_page() + ensure_mys_session(): her goto sonrası CAS giriş ekranı kontrolü.
  Oturum düşerse "MYS girişi bekleniyor" diyip kullanıcı girişini bekler.
  NEDEN: MYS oturumu düşünce kod "Sorgu Kimlik No alanı yok" gibi kriptik hata veriyordu.

### 2026-10-11 — Taşınabilirlik + güvenlik (önceki adımlar)
- resolve_cli(): playwright-cli yolu koda gömülü değil, çalışma anında bulunur.
  NEDEN: kod eski kullanıcı adına (serkan.suc) sabit yola bakıyordu -> bağlantı hiç kurulmuyordu.
- playwright_health() 5 durumlu: OK/NO_CONNECTION/SESSION_CONFLICT/CLI_MISSING/CLI_ERROR.
  NEDEN: "CLI yok" ile "oturum kapalı" ayırt edilmiyordu.
- Excel yolu göreli (data\...) + dosya-yok kontrolü.
- .gitignore: *.xlsx, data/*.xlsx (TCKN/IBAN git'e sızmasın).
- make_test_excel.py: sahte ama geçerli test verisi üretici.

---

## 9. BİLİNEN AÇIK KONULAR / GELECEK İŞ

- Ölü dokümantasyon config'leri (excel-map.json, stage1-fields.json,
  stage1-status.json) koddan okunmuyor — ileride kod/config kayması riski.
- data/mys-main.js (2.1MB) + rt-source.txt + guide-index.html repo'da (vendor şişmesi).
- stage1-flow-run.py, duplicate-check-run.py, excel-read.py legacy/yardımcı — motor kullanmıyor.
- daily (Gündelik Tipi) değeri Excel'den gelir; MYS'deki gerçek seçenek metniyle
  birebir eşleşmeli, yoksa form seçim adımında hata verir.
- Canlı uçtan uca test MYS oturumu gerektirir (otomasyon giriş yapmaz).

```

Bağımlılıklar: Python 3.12 + openpyxl, Node (playwright-cli). Oturum: chrome-main.
Derleme kontrolü: python -m py_compile scripts\<dosya> ve node --check scripts\<dosya>.
