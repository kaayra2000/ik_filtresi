#!/bin/bash

# IK Filtresi Build Script
# Bu script PyInstaller ile uygulamayı derler

echo "==================================="
echo "  IK Filtresi Build Script"
echo "==================================="

# Virtual environment aktif mi kontrol et
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment aktif değil!"
    echo "   Aktifleştirmek için: source .venv/bin/activate"
fi

# PyInstaller yüklü mü kontrol et
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 PyInstaller yükleniyor..."
    pip install pyinstaller
fi

# Versiyon bilgisi (argüman olarak alınır veya varsayılan kullanılır)
VERSION=${1:-"dev"}
echo "📌 Versiyon: $VERSION"

# Versiyon dosyası oluştur
echo "$VERSION" > version.txt
echo "📝 version.txt oluşturuldu"

# Önceki build'i temizle
echo "🧹 Önceki build dosyaları temizleniyor..."
rm -rf build/ dist/

# Build al
echo "🔨 Build alınıyor..."
pyinstaller ik_filtresi.spec --clean

# Sonuç
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build başarılı!"
    echo "📁 Çalıştırılabilir dosya: dist/IK_Filtresi/IK_Filtresi"
    echo ""
    echo "Çalıştırmak için:"
    echo "   ./dist/IK_Filtresi/IK_Filtresi"
else
    echo ""
    echo "❌ Build başarısız!"
    exit 1
fi
