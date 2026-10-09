# MYS YOLLUK OTOMASYONU — PROJE DEVİR / KURTARMA DOSYASI
Tarih: 23.09.2026
Proje klasörü: C:\Users\serkan.suc\Desktop\MYS-YOLLUK-OTOMASYON
Kapsam: AŞAMA 1 — Yolluk Süreç Hazırlama

## 1. AMAÇ
Excel personel listesinden MYS/HYS Yolluk Süreç Hazırlama formlarını otomatik doldurmak, MYS kontrolleriyle doğrulamak ve yetkili canlı çalışmada kaydı güvenli biçimde oluşturmak.

Aşama 1 sınırı:
Excel -> personel doğrulama -> MYS formu -> Birim Amiri sorgusu -> Yolluk Süreç Hazırlama -> sunucu kaydı doğrulama -> Harcama Talimatı oluşumu.

E-imza, Harcama Talimatı onayı ve sonraki manuel onaylar otomasyona dahil değildir.
Aşama 2 Yolluk Bildirim henüz geliştirilmemiştir.

## 2. KULLANICI BEKLENTİSİ
Sistem normalde tamamen otomatik çalışmalı; her alan için onay istememelidir.
Sadece otomasyonun güvenli biçimde kendi başına çözemeyeceği kritik durumlarda kullanıcıya durup bilgi/karar istemelidir.

Hedef kontrol paneli:
- canlı işlem adımları,
- kişi sayısı ve ilerleme,
- hata/uyarı,
- normal adımlarda onay yok,
- kritik durumda pause,
- işlem sonunda özet.
GPT sohbeti otomasyonun çalışması için zorunlu olmamalıdır.

## 3. TEKNİK MİMARİ
Kullanıcı -> MYS Yolluk Otomasyonu kontrol paneli -> yerel otomasyon motoru -> Playwright -> Chrome -> MYS.
Python + JavaScript akışları kullanılıyor.
Chrome/Playwright bağlantısı sistemin temel parçasıdır.
Mevcut Playwright oturumu: chrome-main
CLI: C:\Users\serkan.suc\AppData\Roaming\npm\playwright-cli.cmd
TÜM CLI çağrılarında -s=chrome-main kullanılmalıdır. Başka Playwright oturumu (chrome, chrome-2 vb.) kullanılmaz.
MYS işlemleri DOM/Playwright üzerinden yapılır; koordinat/mouse otomasyonu tercih edilmez.

Desktop Commander Remote:
- cihaz: tsmpc1
- device ID: 9dc6f9ea-52e3-4912-91a9-1df27622af90
- Desktop Commander: 0.2.51
- Node: 24.20.0
- Python: 3.14.4
- Windows / PowerShell.

## 4. MYS ADRESLERİ
Form:
https://butunlesik.hmb.gov.tr/hys/mys-yollukislemleri/yolluk/add
Sorgu:
https://butunlesik.hmb.gov.tr/hys/mys-yollukislemleri/yolluk
Submit endpoint: /yolluk/ekle
Resmi sistem: https://butunlesik.hmb.gov.tr/

## 5. EXCEL
Ana workbook:
C:\Users\serkan.suc\Desktop\YOLLUKLAR\2026\LİSTE 7\Yolluk Liste 7.xlsx

Birinci sayfa personel listesidir.
İkinci sayfa Birim Amiri bilgisini içerir.
Alanlar:
SIRANO, TC NO/TCKN, AD, SOYAD, UNVAN, DERECE, KADEME, EK GÖSTERGE, GÜNDELİĞİ, GEÇ. GÖREV TARİHİ, GÜN SAYISI, IBAN.

Birim Amiri TCKN sabit kodlanmaz.
İkinci sayfada ilk 20 satır içinde TC/TCKN etiketi aranır ve hemen sağındaki 11 haneli değer alınır.
Bulunamazsa USER_INFORMATION_REQUIRED ile durulur.

## 6. SABİT MYS DEĞERLERİ
Yolluk Tipi: Yurtiçi Geçici Görev Yolluğu - Talimatlı
Ödeme Kaynak Türü: Merkezi Yönetim
Ödeme Kaynak Alt Türü: SAĞLIK BAKANLIĞI
Program Türü: TEDAVİ EDİCİ SAĞLIK
Alt Program Türü: TEDAVİ HİZMETLERİ
Faaliyet Türü: Devlet Hastanesi Hizmetleri
Alt Faaliyet Türü: Teşhis ve Tedavi Hizmetleri
Bütçe Tertibi: 54.167.480.17695.14.67.01.03.03.10
Avans: Avans Verilmeyecek

Asıl kaynak config\fixed-values.json'dır.

## 7. FORM İŞLEM SIRASI
1. Yolluk Süreç Hazırlama sayfasını aç.
2. Kimlik No sorgusu.
3. Mernis'ten Güncelle.
4. Maaş Güncelle.
5. Ad Soyad, Unvan, Ek Gösterge, Derece, Kademe doğrula.
6. IBAN'ı Excel ile karşılaştır ve MYS formuna seç.
7. Yolluk Tipi seç.
8. Başlangıç/Bitiş tarihlerini gir.
9. Ödeme Kaynak Türü.10. Ödeme Kaynak Alt Türü.
11. Program Türü.
12. Alt Program Türü.
13. Faaliyet Türü.
14. Alt Faaliyet Türü.
15. Gündelik Tipi.
16. Bütçe Ödenek -> Ekle.
17. Bütçe Tertibi.
18. Avans Durumu.
19. Birim Amiri TCKN gir.
20. Yalnızca Birim Amiri sorgusu yap.
21. Amir Ad Soyad/Unvan geldiğini doğrula.
22. Submit öncesi formu kontrol et.
23. Yolluk Süreç Hazırlama düğmesine canlı modda yalnızca bir kez bas.
24. MYS kaydını Sorgula ile doğrula.

## 8. DERECE / KADEME / GÜNDELİK
Maaş Güncelle sonucu birincil kaynaktır.
MYS değeri dolu ve anlamlıysa kullanılır.
Boş, 0 veya gelmemişse Excel fallback kullanılabilir.
Gerçek çelişkide rastgele seçim yapılmaz; kullanılabilir MYS değeri önceliklidir ve fark loglanır.
İki kaynak da yetersizse durulur.

Testte doğrulanan örnek Gündelik Tipi:
I-B-e) 850.00 Memur ve Hiz.; Aylık/kadro derecesi 5-15 olanlar

## 9. TARİH MANTIĞI
Desteklenen örnekler:
- 01,05,08/09/2026
- 01.09.2026,05.09.2026,08.09.2026- 01-05-08/09/2026
- 01-05-08.09.2026
- 01-30/09/2026

Gerçek görev günleri ayrı tutulur.
MYS başlangıç = en erken gerçek görev günü.
MYS bitiş = en geç gerçek görev gününün ertesi günü.

Örnek:
03,10,12/08/2026 -> gerçek günler 03/08, 10/08, 12/08; MYS 03/08/2026 -> 13/08/2026.

assignmentId = TCKN + Yolluk Tipi + başlangıç + bitiş bilgilerinin SHA-256 özetinin ilk 20 karakteri.
Kişi değil görev kayıt anahtarıdır.

## 10. DUPLICATE / ÇAKIŞMA
Aynı kişi farklı tarihlerde birden fazla yolluk alabilir.
MYS sorgusu önce Sorgula ile tazelenmelidir.
İlişkiler:
- EXACT: aynı görev aralığı
- OVERLAP: tarih kesişmesi
- AMBIGUOUS: tarih güvenle ayrıştırılamadı

Uyarı:
"ÇAKIŞMA UYARISI: Mevcut/çakışan yolluk bulundu. Sistem kullanıcı onayı beklemeden yeni yolluk için devam ediyor."

Uyarı engel değildir; otomasyon kullanıcı onayı beklemeden devam eder. `DUPLICATE_WARNING_CONTINUING` durumuyla checkpoint/log kaydı tutulur.
AMBIGUOUS durum da kullanıcı onayı bekletmez; sınıflandırılamayan tarih bilgisi açık uyarı olarak loglanır ve akış devam eder.

Mevcut örnek kişi için aynı/çakışan canlı kayıt bulunduğu bilinmektedir; tekrar gönderim yapılmamalıdır.
## 11. MYS SORGU KURALI
Yolluk Süreç ana sayfasındaki liste Sorgula yapılmadan güvenilir değildir.
Ana sayfaya her girişte veya dönüşte önce Sorgula yapılmalıdır.
Kayıt sonrası MYS boş/stale liste gösterebilir; bu başarısızlık anlamına gelmez.
Yeni kayıt listenin ilk satırı olduğu için kabul edilmez.
Yeni kayıt kişi + başlangıç + bitiş + baseline kayıt ID'leri ile doğrulanır.

## 12. SUBMIT GÜVENLİĞİ
Durumlar:
SUBMITTING -> SUBMITTED_UNVERIFIED -> STAGE1_COMPLETED

Submit tıklandıktan sonra ikinci tıklama yasaktır.
Ağ/oturum belirsizse yeni form kurma veya tekrar submit yapma.
Önce MYS sorgula ve mevcut kaydı doğrula.
Doğrulanamayan gönderim ERROR/manual-review durumunda kalmalıdır.

## 13. FORM RETRY
MYS Power Select alanları custom bileşenlerdir.
Seçim:
- alanı aç,
- trigger input'u bekle,
- arama metnini yaz,
- görünür seçenek panelini bul,
- gerçek option'a tıkla,
- seçilen etiketi doğrula.

Panel alanın dışına tether edilebilir; son görünür .yte-power-select-options veya [role=listbox] paneli kullanılır.

Bir alan başarısızsa önce yalnızca o alan tekrar denenir.
İkinci deneme başarısızsa form baştan açılıp tümü yeniden doldurulur.İkinci tam deneme başarısızsa ERROR.
Bu retry yalnızca submit öncesidir.
Submit sonrası form retry yapılmaz.

## 14. IBAN
MYS IBAN alanı custom Power Select/tag input'tur.
Excel'deki yeni IBAN dropdown'da bulunmayabilir.
Yeni IBAN için gerçek browser Enter gereklidir.

Keşif:
JavaScript sentetik KeyboardEvent Enter yeterli olmadı.
Playwright gerçek press Enter ile yeni IBAN MYS formuna tag olarak eklendi.

Akış:
1. Eski seçili IBAN varsa kaldır.
2. Excel IBAN'ını yaz.
3. Kayıtlı seçenek varsa gerçek option'a tıkla.
4. Yeni IBAN ise gerçek Playwright Enter uygula.
5. Seçili etiketi doğrula.
6. MYS validator hatası ve submit durumunu doğrula.

MYS frontend IBAN validator:
- ülke kodu,
- ülkeye göre uzunluk,
- MOD-97 checksum.
TR için 26 karakter bekleniyor.
Banka hesabının gerçekten varlığını veya kişiye aitliğini doğruladığına dair frontend kanıtı bulunmadı.

Karar: otomasyona yerel IBAN ön kontrolü eklenecek:
TR + 26 karakter + MOD-97.Geçmezse MYS'ye göndermeden durulabilir.
Nihai doğrulama yine MYS'ye aittir.

Full IBAN değerleri bu belgeye yazılmaz.

## 15. BİLİNEN ENDPOINT'LER
/hys/gateway/yolluk/kisi/getirYollukKisiByTcKimlikNo
/hys/gateway/yolluk/kisi/getirYollukKisiByTcKimlikNoKisiBilgisiSorgulamaServisinden
/hys/gateway/yolluk/kisi/getirMaasKisiByTcKimlikNo
/hys/gateway/yolluk/kisi/getirKisiveMaasByTcKimlikNo
/hys/gateway/yolluk/tertipAlani/program/getirAktifProgramButceList
/hys/gateway/yolluk/tertipAlani/altProgram/getirAktifProgramButceList
/hys/gateway/yolluk/tertipAlani/faaliyet/getirAktifProgramButceList
/hys/gateway/yolluk/gundelikBilgisi/getirGundelikBilgisiList
/hys/gateway/yolluk/odemeKaynakAltTuru/getirOdemeKaynakAltTuruList
/hys/gateway/yolluk/tertipAlani/getirAktifAltFaaliyetList
/hys/gateway/yolluk/odenek/getirOdenekList
/yolluk/ekle

Yeni IBAN Enter sırasında ayrıca network isteği olup olmadığı kesinleştirilmemiştir. Araştırılırsa IBAN değeri loglara açık yazılmamalıdır.

## 16. DOSYALAR
config:
- excel-map.json
- fixed-values.json
- runner-settings.json
- runner-settings.runtime.json
- stage1-fields.json
- stage1-rules.md
- stage1-status.json
data:
- checkpoint.json
- excel-dry-output.json
- guide-index.html
- last-flow.js
- mys-main.js
- rt-source.txt
- session-manifest.json

scripts:
- assignment.py
- assistant-stage1.py
- duplicate-check-run.py
- duplicate-check.js
- excel-read.py
- make_iban_flows.py
- stage1-core.ps1
- stage1-diagnostics.ps1
- stage1-flow-run.py
- stage1-flow.js
- stage1-flow-pre.js
- stage1-flow-post.js
- stage1-live-run.py

tests:
- test-assignment.py

## 17. MEVCUT CHECKPOINT
Mevcut checkpoint: assignmentId: 1a1631142c71d6cee0ee
row: 1
status: READY_TO_SUBMIT
dutyDates: 03,10,12/08/2026
actualDutyDates: 03/08/2026, 10/08/2026, 12/08/2026
mysStart: 03/08/2026
mysEnd: 13/08/2026
approvalGranted: false

Son form/IBAN dry-run tamamlandı; form `Yolluk Süreç Hazırlama` gönderimine hazırlandı ve canlı submit yapılmadı. Bu kişi/tarih aralığı için MYS'de daha önce oluşturulmuş gerçek kayıt bulunduğundan bu assignment canlı olarak tekrar gönderilmemelidir.

Önceden oluşturulmuş gerçek kayıt:
Yolluk No: 1024060
Yolluk Referans No: 2026YLK00059
Tarih: 03/08/2026 -> 13/08/2026
Tekrar oluşturulmamalıdır.

Referans olarak kullanılan tamamlanmış kayıt:
MYS view id=952664
Stage 2/Yolluk Bildirim incelemesinde referans olmuştur.

## 18. SON IBAN TESTİ
Örnek kişinin Excel IBAN'ı kullanıcı tarafından değiştirilmiştir.
MYS eski IBAN'ı otomatik getiriyordu.
Yeni IBAN dropdown'da yoktu.
Gerçek Playwright Enter ile yeni IBAN seçili tag olarak eklendi.
Diğer alanlar dolduruldu.
Birim Amiri FİKRET ARAS / Baştabib olarak geldi.
Son dry-run'da form `Yolluk Süreç Hazırlama` gönderimine hazır duruma geldi; canlı submit yapılmadı.
IBAN için yerel TR + 26 karakter + MOD-97 ön kontrolü artık `stage1-live-run.py` içinde uygulanıyor.

Yeni ajan IBAN'ı bu dosyadan tahmin etmemeli; güncel Excel'den okumalıdır.

## 19. TEST DURUMU
assignment.py + test-assignment.py:
ASSIGNMENT TESTS OK

Form:
- TCKN/Mernis/Maaş çalışıyor.
- Power Select gerçek option click çalışıyor.
- Dinamik kaynak/program/faaliyet alanları çalışıyor.
- Bütçe tertibi seçiliyor.
- Birim Amiri sorgusu çalışıyor.
- Yeni IBAN için gerçek Enter gerektiği kanıtlandı.
- Formun büyük kısmı submit öncesi doluyor.
- Son IBAN testinde canlı submit yapılmadı.

## 20. GÜVENLİK KİLİTLERİ
runner-settings.json:
liveSubmissionEnabled=false
stopBeforeLiveSubmit=true
duplicateProtection=true
onePersonAtATime=true
saveScreenshotsOnError=true

Canlı gönderim ancak kullanıcı açıkça canlı çalışma talep ettiğinde ele alınmalıdır.
E-imza otomatikleştirilmemelidir.
Kimlik doğrulama, 2FA, CAPTCHA veya MYS iş kuralları bypass edilmemelidir.
## 21. YENİ AI AJANININ İLK İŞLERİ
1. Bu dosyayı tamamen oku.
2. Proje klasörü ve config/script dosyalarını incele.
3. runner-settings güvenlik kilitlerini kontrol et.
4. checkpoint.json'u oku.
5. Güncel Excel'i oku; Birim Amiri TCKN ve IBAN'ı oradan al.
6. Chrome/Playwright bağlantısını doğrula.
7. Dry-run/form-test yap.
8. IBAN ön kontrolünü ekle/test et.
9. Duplicate sorgusunun her liste okumasından önce Sorgula yaptığını doğrula.
10. Submit sonrası SUBMITTED_UNVERIFIED ve sorgu ile doğrulamayı koru.
11. Yeni değişiklikten önce yedek al.

## 22. GELECEK GELİŞTİRME PLANI
1. IBAN yerel ön kontrolü.
2. Submit disabled nedenini kesin teşhis.
3. Duplicate/Sorgula sağlamlaştırması.
4. Windows kontrol paneli.
5. Kritik durumlarda pause/resume ve kullanıcı veri girişi.
6. Masaüstü başlatıcı.
7. Otomatik Playwright bağlantı/health check.
8. Aşama 1 canlı stabilizasyon.
9. Aşama 2 Yolluk Bildirim araştırması.
10. GPT destekli üst seviye kontrol katmanı.

## 23. TEMEL PRENSİP
Normal adımlar otomatik.
Gereksiz onay yok.
Belirsizlikte tahmin yok.Kritik mali işlem öncesi güvenlik kontrolü.
Gönderilmiş işlem doğrulanmadan tekrar gönderim yok.
MYS validasyonu bypass edilmez.
Playwright sistemin temel çalışma katmanıdır.
