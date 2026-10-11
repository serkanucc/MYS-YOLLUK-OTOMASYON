# MYS YOLLUK OTOMASYONU — PROJE BİLGİ AĞACI / AI EL KİTABI

> BU DOSYA PROJENİN HAFIZASIDIR. Kod değiştirmeden önce MUTLAKA oku.
> Kodlama kuralı, mimari, güvenlik ilkeleri ve tüm değişiklik günlüğü burada tutulur.
> Son güncelleme: 2026-10-11

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
| `stage1-live-run.py` | **Ana motor.** Excel okur, IBAN/tarih doğrular, mükerrer kontrol, formu doldurur, güvenli submit. | ✅ Aktif |
| `assignment.py` | **Saf mantık.** Tarih çözümleme (`duty_period`), görev kimliği (`assignment_id`), çakışma sınıflandırma (`classify_candidates`). Testli. | ✅ Aktif |
| `yolluk-controller.py` | **Kontrol paneli** (http://127.0.0.1:8765). Durum, canlı adımlar, log, başlat/durdur. | ✅ Aktif |
| `yolluk-panel.bat` | Paneli başlatır (port açıksa sadece tarayıcı açar). | ✅ Aktif |
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
| `test-assignment.py` | `assignment_id` + `classify_candidates` (EXACT/OVERLAP). |
| `test-read-amir.py` | `read_amir_tckn` (2. sayfa, TCKN temizliği). |

---

## 3. ANA AKIŞ (stage1-live-run.py main → tamamlanma)

1. CLI çözümleme (`resolve_cli`): config → PATH → %APPDATA%. Yoksa None.
2. Bağlantı kontrolü (`wait_for_playwright`): CLI_MISSING ise HATA, değilse OK bekle.
3. Excel okuma (`people`): dosya yoksa net hata; SATIR BAZLI HATA DAYANIKLI
   (bozuk satırı atla+logla, `EXCEL_ROW_SKIPPED`).
4. Her personel için: STAGE1_COMPLETED ise atla → save(PROCESSING) →
   `duplicate(x)` (Sorgula) → `classify_candidates` (EXACT/OVERLAP/AMBIGUOUS,
   uyarı ama ENGEL DEĞİL) → baseline_ids topla → form doldur (js_pre → IBAN Enter →
   js_post, 2 deneme) → READY_TO_SUBMIT → canlı değilse dur → güvenlik kilidi →
   canlıysa tek tık → SUBMITTING → SUBMITTED_UNVERIFIED → STAGE1_COMPLETED
   (doğrulama: baseline ID + tam tarih, sıraya GÜVENME).

---

## 4. GÜVENLİK İLKELERİ (DEĞİŞTİRME)

- Canlı gönderim ÇİFT KİLİTLİ: liveSubmissionEnabled=false + --stop-before-submit.
- Submit butonuna TEK TIK; ikinci tık yasak; belirsizlikte yeniden tıklama YOK.
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
python tests\test-assignment.py           # ASSIGNMENT TESTS OK
python tests\test-read-amir.py            # READ_AMIR_TCKN TESTS OK

## 8. DEĞİŞİKLİK GÜNLÜĞÜ (CHANGELOG) — en yenisi üstte

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


