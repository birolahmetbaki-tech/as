@echo off
rem Veritabaninin guvenli yedegini backups klasorune alir.
rem Uygulama acikken de calistirilabilir.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo Kurulum tamamlanmamis: .venv klasoru bulunamadi.
  echo README.md icindeki Kurulum adimlarini uygulayin.
  echo.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" scripts\backup.py
echo.
pause
