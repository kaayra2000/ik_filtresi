# İK Filtresi (İnsan Kaynakları Aday Filtreleme Aracı)

## Genel Bakış
İK Filtresi, İnsan Kaynakları departmanlarının işe alım süreçlerini hızlandırmak ve kolaylaştırmak için tasarlanmış bir masaüstü uygulamasıdır. Bu araç sayesinde, büyük aday listelerini (Excel veya CSV formatında) saniyeler içinde yükleyebilir, belirlediğiniz kriterlere göre filtreleyebilir ve sonuçları kaydedebilirsiniz.

## Temel Özellikler

*   **Kolay Veri Yükleme:** Aday verilerini içeren Excel (.xlsx, .xls) veya CSV dosyalarını sürükleyip bırakarak veya dosya seçici ile hızlıca yükleyin.
*   **Gelişmiş Filtreleme:** Adayları çeşitli kriterlere (örneğin; deneyim süresi, eğitim durumu, bildiği diller vb.) göre filtreleyin.
*   **Esnek Kriter Yönetimi:** İhtiyaçlarınıza göre filtreleme kriterlerini (aralıklar, anahtar kelimeler) kolayca ayarlayın.
*   **Sonuçları Dışa Aktarma:** Filtrelenmiş aday listesini yeni bir Excel veya CSV dosyası olarak bilgisayarınıza kaydedin.
*   **Kullanıcı Dostu Arayüz:** Teknik bilgi gerektirmeyen, anlaşılır ve sade bir arayüz ile herkes tarafından rahatlıkla kullanılabilir.

## Nasıl Kullanılır?

1.  Uygulamayı başlatın.
2.  "Dosya Yükle" butonunu kullanarak veya sürükle-bırak yöntemiyle aday listenizi programa tanıtın.
3.  Sol paneldeki filtreleme seçeneklerini kullanarak istediğiniz kriterleri belirleyin.
4.  "Filtrele" butonuna basarak sonuçları görüntüleyin.
5.  Listelenen sonuçları "Dışa Aktar" seçeneği ile kaydedin.

## Kurulum ve Çalıştırma

Bu uygulama **Windows, macOS ve Ubuntu (Linux)** işletim sistemlerinde sorunsuz çalışmaktadır.

### Gereksinimler
*   Python 3.8 veya üzeri

### Geliştirme Ortamı Kurulumu
Projeyi yerel makinenizde çalıştırmak veya geliştirmek için aşağıdaki adımları izleyin:

1.  **Gerekli kütüphaneleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Uygulamayı başlatın:**
    ```bash
    python main.py
    ```

### Çalıştırılabilir Dosya Oluşturma (Build)
Uygulamayı tek bir çalıştırılabilir dosya (.exe veya binary) haline getirmek için işletim sisteminize uygun betiği kullanabilirsiniz:

*   **Windows için:**
    ```cmd
    build.bat
    ```
    Bu işlem `dist` klasörü altında bir `.exe` dosyası oluşturacaktır.

*   **macOS / Ubuntu (Linux) için:**
    ```bash
    chmod +x build.sh
    ./build.sh
    ```
    Bu işlem `dist` klasörü altında çalıştırılabilir bir dosya oluşturacaktır.
