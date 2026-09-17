@echo off
rem Enerji Izleme uygulamasini baslatir ve tarayicida acar.
rem Uygulamayi durdurmak icin bu pencereyi kapatin.
cd /d "%~dp0"

if not exist ".venv\Scripts\uvicorn.exe" (
  echo.
  echo Kurulum tamamlanmamis: .venv klasoru bulunamadi.
  echo README.md icindeki Kurulum adimlarini uygulayin.
  echo.
  pause
  exit /b 1
)

if not exist ".env" (
  echo.
  echo .env dosyasi yok. .env.example dosyasini .env olarak kopyalayip
  echo SECRET_KEY ve APP_PASSWORD_HASH degerlerini doldurun.
  echo.
  pause
  exit /b 1
)

rem Sunucu ayaga kalkana kadar bekle, sonra tarayiciyi ac.
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8000"
echo Uygulama calisiyor: http://127.0.0.1:8000
echo Durdurmak icin bu pencereyi kapatin veya Ctrl+C yapin.
echo.
".venv\Scripts\uvicorn.exe" app.main:app
pause
