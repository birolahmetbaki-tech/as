@echo off
rem Enerji Izleme uygulamasini baslatir ve tarayicida acar.
rem Uygulamayi durdurmak icin bu pencereyi kapatin veya Ctrl+C yapin.
cd /d "%~dp0"

if not exist ".venv\Scripts\uvicorn.exe" (
  echo.
  echo Kurulum tamamlanmamis: .venv klasoru bulunamadi.
  echo README.md icindeki Kurulum adimlarini uygulayin.
  echo.
  pause
  exit /b 1
)

rem Ortam denetimi: .env, SECRET_KEY, APP_PASSWORD_HASH ve veritabani tablolari.
".venv\Scripts\python.exe" scripts\onkontrol.py
if errorlevel 1 (
  pause
  exit /b 1
)

rem Sunucu hazir olunca tarayiciyi ac (sabit bekleme yok, /saglik yoklanir).
start "" /b ".venv\Scripts\python.exe" scripts\tarayici_ac.py

echo Uygulama calisiyor: http://127.0.0.1:8000
echo Durdurmak icin bu pencereyi kapatin veya Ctrl+C yapin.
echo.
".venv\Scripts\uvicorn.exe" app.main:app

if errorlevel 1 (
  echo.
  echo Sunucu baslatilamadi.
  echo En sik neden: 8000 portu baska bir program tarafindan kullaniliyor
  echo (uygulama zaten acik olabilir). Acik pencereleri kapatip tekrar deneyin.
  echo.
)
pause
