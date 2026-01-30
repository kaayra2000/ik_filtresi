# App Package

## Genel Bakış
`app` paketi, İK Filtresi uygulamasının ana kaynak kodlarını barındırır. Uygulama mantığı, veri modelleri ve kullanıcı arayüzü bileşenleri bu dizin altında modüler bir yapıda organize edilmiştir.

## Dizin Yapısı

Bu paket aşağıdaki alt paketlerden oluşur:

*   **`models/`**: Uygulamanın veri yapılarını ve veritabanı/bellek içi nesne modellerini içerir. Verilerin nasıl saklandığını ve taşındığını tanımlar.
*   **`services/`**: İş mantığını (business logic) içeren servisleri barındırır. Dosya okuma/yazma, filtreleme algoritmaları ve veri analiz işlemleri burada yapılır.
*   **`ui/`**: Kullanıcı arayüzü (GUI) bileşenlerini içerir. PyQt6 kullanılarak oluşturulan pencereler, wigdet'lar ve stil dosyaları burada bulunur.

## Ana Dosyalar

*   **`__init__.py`**: Bu dizini bir Python paketi olarak işaretler.
