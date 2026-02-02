# IK Filtresi - Kullanım Kılavuzu

## 📌 Ne İşe Yarar?

IK Filtresi, Excel ve CSV dosyalarındaki verileri hızlı ve kolay bir şekilde filtrelemenizi sağlayan bir araçtır. Özellikle büyük veri kümelerinde arama yaparken ve belirli kriterlere göre veri ayıklamak istediğinizde kullanışlıdır.

---

## 🚀 Nasıl Kullanılır?

### 1. Dosya Açma
- **Dosya → Aç** menüsünden veya **Ctrl+O** kısayoluyla dosya seçin
- Desteklenen formatlar: `.xlsx`, `.xls`, `.csv`
- Uygulama açılınca otomatik olarak dosya seçim penceresi açılır

### 2. Veri Görüntüleme
- Dosya yüklendikten sonra veriler tablo halinde görüntülenir
- Sütun başlıklarına tıklayarak sıralama yapabilirsiniz
- **Sütun Ayrıntıları** butonuyla her sütunun tipi ve istatistiklerini görebilirsiniz

### 3. Filtreleme
- **Filtreler** butonuna tıklayın
- Filtrelemek istediğiniz sütunu seçin
- Filtre türünü belirleyin:
  - **Sayısal:** Eşittir, Büyüktür, Küçüktür, Arasında vb.
  - **Metin:** İçerir, İle Başlar, İle Biter, Eşittir vb.
  - **Tarih:** Önce, Sonra, Arasında vb.
- Birden fazla filtre ekleyebilirsiniz (VE/VEYA mantığıyla)

### 4. Kaydetme
- **Dosya → Kaydet** menüsünden istediğiniz formatı seçin
- **Ctrl+S:** Excel (.xlsx) olarak kaydet
- **Ctrl+Shift+S:** CSV olarak kaydet
- Sadece filtrelenmiş veriler kaydedilir

---

## ⌨️ Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| Ctrl+O | Dosya Aç |
| Ctrl+S | Excel Olarak Kaydet |
| Ctrl+Shift+S | CSV Olarak Kaydet |
| Ctrl+Q | Çıkış |

---

## 💡 İpuçları

- **Büyük dosyalar** için yükleme biraz zaman alabilir, progress bar'ı takip edin
- **Tarih sütunları** otomatik algılanır ve tarih filtresi kullanılabilir hale gelir
- **Tema değişikliği** için Tema menüsünden Açık/Koyu tema seçebilirsiniz
- Filtreler **kaydedilmez**, uygulama kapandığında sıfırlanır

---

## ❓ Sık Sorulan Sorular

**S: Dosyam açılmıyor, ne yapmalıyım?**
- Dosyanın başka bir programda açık olmadığından emin olun
- Dosya formatının desteklendiğini kontrol edin (.xlsx, .xls, .csv)

**S: Filtrelediğim veriler neden kaydedilmiyor?**
- Kaydetme işlemi sadece ekranda görünen (filtrelenmiş) verileri kaydeder
- Tüm veriyi kaydetmek için önce filtreleri temizleyin

**S: Türkçe karakterler bozuk görünüyor?**
- CSV dosyaları için UTF-8 kodlaması kullanıldığından emin olun
