@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ===================================
echo   IK Filtresi Build Script
echo ===================================
echo.

:: Virtual environment kontrolü
if "%VIRTUAL_ENV%"=="" (
    echo [UYARI] Virtual environment aktif degil!
    echo         Aktiflesirmek icin: .venv\Scripts\activate
    echo.
)

:: PyInstaller kontrolü
where pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] PyInstaller yukleniyor...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [HATA] PyInstaller yuklenemedi!
        pause
        exit /b 1
    )
)

:: Versiyon bilgisi (arguman olarak alinir veya varsayilan kullanilir)
set "VERSION=%~1"
if "%VERSION%"=="" set "VERSION=dev"
echo [INFO] Versiyon: %VERSION%

:: Versiyon dosyasi olustur
echo %VERSION%> version.txt
echo [INFO] version.txt olusturuldu

:: Önceki build'i temizle
echo [INFO] Onceki build dosyalari temizleniyor...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Build al
echo [INFO] Build aliniyor...
pyinstaller ik_filtresi.spec --clean

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===================================
    echo   BUILD BASARILI!
    echo ===================================
    echo.
    echo Calistirilabilir dosya:
    echo   dist\IK_Filtresi\IK_Filtresi.exe
    echo.
    echo Calistirmak icin:
    echo   dist\IK_Filtresi\IK_Filtresi.exe
    echo.
) else (
    echo.
    echo ===================================
    echo   BUILD BASARISIZ!
    echo ===================================
    echo.
    pause
    exit /b 1
)

pause
