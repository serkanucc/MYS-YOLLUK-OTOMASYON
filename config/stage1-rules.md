# MYS Yolluk Otomasyon — Aşama 1 Kuralları

## Amaç
Excel personel listesinden MYS Yolluk Süreç Hazırlama kaydını güvenli biçimde oluşturmak.

## Derece / Kademe / Ek Gösterge
Maaş Güncelle sonucu birincil kaynaktır.
MYS değeri dolu ve anlamlıysa MYS değeri kullanılır.
MYS değeri boş, 0 veya gelmemişse ilgili alan için Excel değeri fallback olarak kullanılır.
Gündelik Tipi seçiminde kullanılacak personel verisi bu birleşik kaynaktan üretilir.
Hem MYS hem Excel gerekli bilgiyi sağlamıyorsa otomasyon seçim yapmaz ve güvenli noktada durur.

## Güvenlik
Otomasyon farklı derece/kademe veya gündelik tipi değerini kendi başına uydurmaz.
MYS ve Excel arasında gerçek bir çelişki varsa, MYS değeri kullanılabilir olduğu sürece MYS önceliklidir; fark ayrıca loglanır.
E-imza işlemi Aşama 1 kapsamı dışındadır.

## Aşama 1 akışı
Excel -> doğrulama -> personel kilidi -> Kimlik No -> Mernis Güncelle -> Maaş Güncelle -> veri birleştirme -> IBAN -> Yolluk Tipi -> tarihler -> ödeme kaynakları -> bütçe -> avans -> Gündelik Tipi -> MYS doğrulaması -> Yolluk Süreç Hazırlama -> kayıt doğrulaması.

## Örnek Excel alanları
SIRANO, TC NO, AD, SOYAD, UNVAN, GELDİĞİ KURUM, GEÇ. GÖREV ÇALIŞTIĞI KURUM, DERECE, KADEME, EK GÖSTERGE, GÜNDELİĞİ, GEÇ. GÖREV TARİHİ, GÜN SAYISI, IBAN, Yolluk Tutar.
