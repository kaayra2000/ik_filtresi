# UI Paketi

Bu paket, uygulamanın kullanıcı arayüzünü (GUI) oluşturan bileşenleri içerir. Arayüz PyQt6 kütüphanesi ile geliştirilmiştir.

## Dosyalar ve Görevleri

*   **`main_window.py`**:
    *   Uygulamanın ana penceresidir.
    *   Diğer tüm widget'ları (dosya yükleme alanı, filtre paneli, veri tablosu) bir arada tutar ve yönetir.

*   **`filter_widget.py`**:
    *   Sol taraftaki filtreleme panelini oluşturur.
    *   Kullanıcının yeni filtre eklemesine, düzenlemesine ve silmesine olanak tanır.

*   **`data_table_widget.py`**:
    *   Yüklenen ve filtrelenen verilerin görüntülendiği tablodur.
    *   Veri önizlemesini sağlar.

*   **`column_info_widget.py`**:
    *   Sütun bilgilerinin ve tiplerinin görüntülendiği veya düzenlendiği arayüz bileşenidir.
