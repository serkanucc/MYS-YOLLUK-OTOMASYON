MYS YOLLUK OTOMASYON - AŞAMA 1

MİMARİ
- Ana motor arka planda çalışan yerel otomasyon katmanıdır.
- ChatGPT sohbeti bu motorun orkestrasyon/adaptör katmanıdır.
- Kullanıcı Excel'i hazırlar ve MYS/Chrome oturumunu açar; sohbetten çalıştırma talimatı verir.
- İleride sohbet olmadan aynı motor servis/arayüz üzerinden çalışabilecek şekilde ayrıştırılmıştır.
- E-imza ve Harcama Talimatı onayı otomasyona dahil değildir.

GÖREV KİMLİĞİ
- Kayıt anahtarı kişi değil GÖREV'dir.
- assignmentId = TCKN + Yolluk Tipi + Başlangıç + Bitiş bilgilerinin güvenli özeti.
- Aynı kişinin farklı tarihteki görevi yeni görevdir.
- Checkpoint görev bazlıdır; kişi bazlı değildir.

ÇAKIŞMA / AYNI GÜN UYARISI
- MYS sorgusu önce aynı TCKN kayıtlarını getirir.
- Tarihler birebir aynıysa EXACT uyarısı üretilir.
- Tarihler kesişiyorsa OVERLAP uyarısı üretilir.
- Bir personel için birden çok yolluk kaydı bulunabilir; aynı tarih aralığında dahi yeni işlem açılabilir. Bu durum hata değildir, yalnızca bilgilendirme amaçlıdır.
- Tarih ayrıştırılamıyorsa AMBIGUOUS olarak sınıflandırılır; bu durum kullanıcı onayı beklemez, açık bilgi ile loglanarak devam edilir.
- Uyarı engel değildir: mevcut/kayıt bilgisi kontrol panelinde açıkça gösterilir ve otomasyon onay beklemeden devam eder.
- Onay checkpoint'i kullanılmaz; `DUPLICATE_WARNING_CONTINUING` durumu ile bilgi kayda alınır.
- Bu yapı geriye dönük eksik ödeme düzeltmelerini mümkün bırakır.

DOSYALAR
- scripts\stage1-live-run.py : Aşama 1 üretim motoru
- scripts\stage1-flow.js : MYS form akışı
- scripts\duplicate-check.js : MYS mevcut kayıt sorgusu
- scripts\assignment.py : görev kimliği ve tarih çakışma motoru
- scripts\assistant-stage1.py : ChatGPT tarafından çağrılacak orkestrasyon giriş noktası
- scripts\excel-read.py : Excel doğrulama/okuma
- data\checkpoint.json : görev bazlı devam durumu
- data\session-manifest.json : sohbet kontrollü çalışma manifesti
- tests\test-assignment.py : görev/çakışma birim testleri

GÜVENLİ ÇALIŞMA
- Canlı gönderim varsayılan olarak kapalıdır.
- Kullanıcı açık canlı onayı vermeden gerçek kayıt oluşturulmaz.
- Mevcut kayıt bilgisi engel değildir; kullanıcı onayı gerekmez, otomasyon devam eder.
- Yolluk Süreç ana sayfasındaki liste, Sorgula yapılmadan güvenilir kabul edilmez.
- Ana sayfaya her girişte/geri dönüşte liste okunacaksa MUTLAKA Sorgula yapılır ve sonuç yenilenir.
- Kayıt sonrası MYS'nin boş listeyle ana sayfaya dönmesi normaldir; kayıt başarısız kabul edilmez, önce Sorgula yapılır.
- Kayıt butonuna basıldıktan sonra ikinci kez basılmaz; belirsizlikte önce MYS Sorgula ile kayıt aranır.
- SUBMITTING -> SUBMITTED_UNVERIFIED -> STAGE1_COMPLETED durumlarıyla kayıt gönderimi checkpoint'e alınır.
- Yeni kayıt doğrulaması listenin sırasına değil, mevcut kayıt ID'lerinden ayrıştırılmış yeni kayıt ve görev tarihleri eşleşmesine dayanır.
- Ağ/oturum belirsizliğinde tekrar gönderim yerine önce MYS sorgusu yapılır.
- Tek görev işlenir; hata güvenli checkpoint'e yazılır.

BİRİM AMİRİ
- Yolluk Süreç Hazırlama düğmesine basılmadan önce son otomatik adım Birim Amiri tanımlamasıdır.
- Birim Amiri TCKN her çalıştırmada Excel'in 2. sayfasından okunur; sabit kodlanmaz.
- 2. sayfada TC/TCKN etiketinin sağındaki 11 haneli değer alınır; amir değişirse yalnızca Excel güncellenir.
- MYS'de Birim Amiri TCKN alanına değer yazılır ve yalnızca Birim Amiri sorgusu yapılır.
- Sorgu sonucunda Birim Amiri Ad Soyad gelmezse süreç güvenli biçimde durur ve kullanıcıdan bilgi ister; Yolluk Süreç Hazırlama düğmesine basılmaz.
- Amir TCKN bilgisi Excel'de yoksa USER_INFORMATION_REQUIRED durumuyla kullanıcıya açık bilgi talebi verilir.

AŞAMA 1 SINIRI
Excel -> kişi bilgileri -> MYS formu -> Birim Amiri sorgusu/tanımlaması -> Yolluk Süreç Hazırlama -> sunucu kaydı doğrulama -> Harcama Talimatı oluşumuna kadar.
Harcama Talimatı e-imza/onay işlemi kullanıcıdadır.

GELİŞİM HEDEFİ
Yerel motor ile sohbet katmanı birbirinden bağımsız tutulur. Böylece önce sohbet üzerinden güvenli şekilde dinamik MYS davranışları kontrol edilir; yeterli gözlem ve test biriktikçe aynı motorun sohbet gerektirmeyen otomatik çalışma moduna geçirilmesi mümkün olur.

FORM DOLDURMA / SEÇİMLİ ALANLAR
- Seçimli alanlarda sabit kısa bekleme yerine alanın açılması ve seçenek panelinin gerçekten görünür olması beklenir.
- Arama kutusuna metin yazılsa bile bu metin seçilmiş kabul edilmez; görünür seçenek panelindeki gerçek seçenek tıklanır.
- Seçenek paneli MYS tarafından alanın dışına taşınabildiği için seçim, yalnızca alanın kendi DOM'u değil, o anda görünür olan son Power Select seçenek paneli üzerinden yapılır.
- Seçim tıklandıktan sonra alan içindeki gerçek seçili etiket doğrulanır.
- Dinamik bağımlı alanlarda (Kaynak Alt Türü -> Program -> Alt Program -> Faaliyet -> Alt Faaliyet) alanlar arasında daha uzun bekleme ve yeniden deneme uygulanır.
- Bir seçim ilk denemede yüklenmezse aynı alan en fazla bir kez daha açılıp doldurulur.
- Aynı alan ikinci denemede de çözülemezse form baştan açılır ve tüm girişler yeniden yapılır. Kısmi formu zorla devam ettirmeyiz; MYS formu güvenli biçimde yeniden oluşturulur.
- Formun baştan kurulması yalnızca seçim/alan doldurma aşamasındadır; Yolluk Süreç Hazırlama düğmesine basıldıktan sonra kesinlikle uygulanmaz.
- Submit öncesi her zaman READY_TO_SUBMIT doğrulaması yapılır. Submit sonrası belirsizlikte yeniden tıklama yapılmaz.
- Form doldurma hataları FORM_FILL_RETRY olarak loglanır; ikinci tam form denemesi de başarısızsa ERROR checkpoint ile durur.
