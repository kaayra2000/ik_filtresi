# AGENT.md - Proje Geliştirme Kuralları

Bu belge, "İK Filtresi" projesinde kod yazan Yapay Zeka (AI) asistanları ve geliştiriciler için uyulması **ZORUNLU** kuralları ve rehberleri içerir.

## Proje Hakkında
İK Filtresi, İnsan Kaynakları süreçlerini otomatize eden, aday verilerini yükleyip filtrelemeye ve raporlamaya yarayan bir Python/PyQt6 masaüstü uygulamasıdır.

## Teknoloji Yığını
*   **Dil:** Python 3
*   **GUI:** PyQt6
*   **Veri İşleme:** Pandas

## Mimari ve Tasarım Prensipleri
Bu projede temiz kod, sürdürülebilirlik ve genişletilebilirlik esastır. Aşağıdaki prensiplere **kesinlikle** uyulmalıdır:

### 1. SOLID Prensipleri
Tüm sınıflar ve modüller SOLID prensiplerine uygun tasarlanmalıdır:
*   **SRP:** Her sınıfın tek bir sorumluluğu olmalıdır. (Örn: Veri okuma işi `FileReader` sınıfında, GUI işi `MainWindow` sınıfında).
*   **OCP:** Sınıflar geliştirmeye açık, değişime kapalı olmalıdır. Yeni bir filtre tipi eklendiğinde mevcut kod değiştirilmek yerine yeni bir sınıf türetilmelidir.
*   **LSP:** Alt sınıflar, üst sınıfların yerine geçebilmelidir.
*   **ISP:** Arayüzler (Interfaces) özelleşmiş olmalı, gereksiz metodlar barındırmamalıdır.
*   **DIP:** Üst seviye modüller, alt seviye modüllere bağımlı olmamalıdır; her ikisi de soyutlamalara bağımlı olmalıdır.

### 2. Tasarım Kalıpları (Design Patterns)
Spagetti koddan kaçınılmalı, uygun yerlerde tasarım kalıpları kullanılmalıdır:
*   **Factory Pattern:** Nesne oluşturma süreçleri karmaşıksa (örneğin farklı dosya tipleri için okuyucular), Factory kullanılmalıdır.
*   **Strategy Pattern:** Filtreleme mantıkları gibi değiştirilebilir algoritmalar için Strategy kalıbı kullanılmalıdır.
*   **Observer Pattern:** Veri değiştiğinde arayüzün güncellenmesi gibi durumlar için Observer/Signal-Slot mekanizması etkin kullanılmalıdır.

### 3. Kod Kalitesi
*   **Tip Belirleme (Type Hinting):** Fonksiyon parametreleri ve dönüş değerleri için mutlaka Python Type Hints kullanılmalıdır.
*   **Dokümantasyon:** Her sınıf ve önemli fonksiyonun ne yaptığına dair docstring bulunmalıdır.
*   **İsimlendirme:** Değişken ve fonksiyon isimleri İngilizce, açıklayıcı ve Python standartlarına (snake_case) uygun olmalıdır. Sınıf isimleri PascalCase olmalıdır.

## Klasör Yapısı ve Modülarite
Kodlar işlevlerine göre `app/models`, `app/services`, `app/ui` gibi klasörlere ayrılmıştır. Bu yapı bozulmamalı, yeni dosyalar uygun klasörlere eklenmelidir. Gerekirse yeni klasörler oluşturulabilir.
