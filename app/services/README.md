# Services Paketi

Bu paket, uygulamanın çekirdek iş mantığını (backend logic) yürüten modülleri içerir.

## Dosyalar ve Görevleri

*   **`file_reader.py`**:
    *   Excel (`.xlsx`, `.xls`) ve CSV dosyalarını okumaktan sorumludur.
    *   Pandas kütüphanesini kullanarak veriyi DataFrame formatına dönüştürür.

*   **`file_writer.py`**:
    *   Filtrelenmiş verileri Excel veya CSV formatında diske kaydeder.
    *   Veri dışa aktarma işlemlerini yönetir.

*   **`filter_engine.py`**:
    *   Asıl filtreleme işleminin yapıldığı motordur.
    *   Veri seti üzerinde, kullanıcı tarafından belirlenen kriterleri uygulayarak eşleşen kayıtları döndürür.

*   **`data_analyzer.py`**:
    *   Yüklenen veriyi analiz eder.
    *   Sütunların veri tiplerini, boş değer oranlarını ve benzersiz değerlerini tespit eder.

*   **`filter_persistence.py`**:
    *   Kullanıcının oluşturduğu filtre ayarlarını kaydetmesini ve daha sonra tekrar yüklemesini sağlar (JSON vb. formatlarda).
