# TÜBİTAK 1001 — 124F362 — İP4 teknik rapor çalışma metni

## 1. Amaç ve kapsam

İş Paketi 4 kapsamında, NIST SP 800-90B referans entropi değerlendirmesi ile projede geliştirilen entropi ve sağlık testi yöntemlerini birlikte çalıştırabilen modüler bir test paketinin gerçekleştirilmesi hedeflenmektedir. Başvuru formunda testlerin korelasyon sonuçları dikkate alınarak verimli sağlık testi paketi seçilmesi, yazılımın C ile geliştirilmesi ve bir kullanıcı arayüzü sağlanması açık gerekliliklerdir.

## 2. İlk prototipin gerçekleştirilmesi

GUI için Python Tkinter, referans değerlendirmeler için derlenmiş NIST `ea_iid` ve `ea_non_iid` programları, araştırma amaçlı RCT/APT gerçekleştirmesi için C11 kullanılmıştır. GUI girişleri doğrular, her veriyi NIST uyumlu byte-per-symbol temsiline çevirir, harici programları ayrı işlem olarak çağırır ve çıktılarını değişmeden saklar. Batch işleme ve sonuç dosyaları sağlanmıştır. GUI'nin Python ile uygulanması, başvuru formundaki C beklentisinin bütün test paketleri için karşılandığı anlamına gelmemektedir: yalnızca sağlık prototip motoru C ile gerçekleştirilmiştir.

## 3. Entropi tanımları

Min-entropi: H_inf(X) = -log2(max_x P(X=x)). Shannon entropisi: H(X) = -sum_x P(X=x)log2 P(X=x). İki kavramın eşdeğer olmadığı, özellikle zamansal bağımlılık altında marjinal dağılım ölçümlerinin kaynak öngörülemezliğini tam açıklayamayabileceği dikkate alınacaktır. Prototip C modülündeki ampirik hesaplar plug-in betimsel istatistiklerdir; NIST güvenlik entropi tahminleri değildir.

## 4. Deney protokolü

Bit genişlikleri 1, 4, 8; her veri setinde 1.000.000 sembol. Sentetik senaryolar: uniform IID, yanlı IID, Markov bağımlılığı, sabit değere kilitlenme, periyodik örüntü. Her ailenin tekrarlanabilir başlangıç tohumu manifestte kayıt altına alınacaktır. IID varsayımı uygun değilse uniform dağılımın marjinal min-entropisi, süreç için güvenlik entropisi gibi raporlanmayacaktır.

İlk bilimsel tablolar: (i) veri seti kimliği/türü, (ii) IID testlerinin çıktı ayrıntıları, (iii) non-IID tahmincilerinin kendi değerleri, (iv) RCT/APT alarm oranları, (v) işlem süreleri. Test istatistikleri ve entropi değerleri NIST ham çıktı formatı doğrulanarak ayrıştırılmalıdır. İkinci fazda özgün entropi tahmincileri ve yeni sağlık testlerinin eklenmesi, kontrollü bozulmalar altında tespit oranı, yanlış pozitif oranı ve alarm gecikmesi ile korelasyon matrisinin hesaplanması hedeflenmektedir.

## 5. Deney sonuçları

**Henüz doldurulmadı.** Gerçek cihazda deney yürütülmeden sayısal sonuç, doğruluk ve hız iddiası yazılmamalıdır. Bu bölüme `results.json`, ham NIST günlükleri, karşılaştırmalı grafikler ve deney metaverileri üzerinden doğrulanmış sayılar eklenecektir.

## 6. Sınırlılıklar ve kalan İP4 çalışmaları

İP1 özgün tahmincilerinin formüllerinin yazılımsal doğrulanması, İP3 yeni sağlık testleri, FIPS karşılaştırmaları, korelasyon temelli seçim, NIST 800-90B restart/conditioner değerlendirmeleri ilgili kaynak türüne göre ele alınmalı; uçtan uca C motoru ve Windows/Linux/macOS paketleme testleri tamamlanmalıdır. RCT/APT eşiklerinin SP 800-90B Bölüm 4 ile uyumlu türetilmesi ve arızalarda alarm sınırlarının denetlenmesi gerekmektedir.

## 7. Referanslar

[1] NIST SP 800-90B, *Recommendation for the Entropy Sources Used for Random Bit Generation* (2018), Sections 3–6, doi:10.6028/NIST.SP.800-90B.

[2] TÜBİTAK 1001 Proje Başvuru Formu, Proje 124F362, İP4 tablosu.

[3] TÜBİTAK 1001 Birinci Bilimsel Gelişme Raporu, Proje 124F362.
