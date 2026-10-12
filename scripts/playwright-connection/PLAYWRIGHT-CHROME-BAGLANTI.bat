@echo off
title Playwright - Chrome Baglantisi
color 0A
setlocal
set "PLAYWRIGHT_CLI_SESSION=chrome-main"
if not defined PLAYWRIGHT_CLI_JS (
  for /f "delims=" %%I in ('npm root -g 2^>nul') do set "PLAYWRIGHT_NPM_ROOT=%%I"
  if defined PLAYWRIGHT_NPM_ROOT set "PLAYWRIGHT_CLI_JS=%PLAYWRIGHT_NPM_ROOT%\@playwright\cli\playwright-cli.js"
)
if not exist "%PLAYWRIGHT_CLI_JS%" set "PLAYWRIGHT_CLI_JS=%APPDATA%\npm\node_modules\@playwright\cli\playwright-cli.js"
if not exist "%PLAYWRIGHT_CLI_JS%" (
  echo playwright-cli.js bulunamadi. Playwright CLI kurulumunu kontrol edin.
  goto SON
)
set "PLAYWRIGHT_MCP_OUTPUT_DIR=%TEMP%\playwright-cli-output"

echo ================================================
echo   PLAYWRIGHT - CHROME BAGLANTISI
echo ================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0PW-SESSION-GUARD.ps1"
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" goto AKTIF
if "%RC%"=="20" goto ATTACH
if "%RC%"=="40" goto REATTACH
if "%RC%"=="30" goto CONFLICT

echo PLAYWRIGHT GUARD HATASI. Yeni session ACILMADI.
echo Hata kodu: %RC%
goto SON

:AKTIF
echo.
echo Aktif chrome-main + yesil Playwright baglantisi dogrulandi.
echo Yeni Allow ^& select ekrani ACILMAYACAK.
goto SON

:ATTACH
echo.
echo Aktif Playwright baglantisi yok.
echo Allow ^& select ekrani aciliyor...
echo Session adi: chrome-main
echo.
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0PW-START-ATTACH.ps1"
echo Chrome icindeki Allow ^& select adimini tamamlayin.
goto SON

:REATTACH
echo.
echo chrome-main mevcut fakat yesil Playwright grubu yok.
echo Mevcut attach guvenli sekilde ayriliyor; Chrome kapatilmiyor.
node "%PLAYWRIGHT_CLI_JS%" -s=chrome-main detach >nul 2>&1
timeout /t 1 /nobreak >nul
goto ATTACH

:CONFLICT
echo.
echo PLAYWRIGHT BAGLANTI DURUMU TUTARSIZ.
echo Yeni session ACILMADI.
echo Mevcut uyumsuz sessionlar tamamen temizlenemedi.
echo Once mevcut sessionlari kontrol etmek gerekiyor.
goto SON

:SON
echo.
echo Bu CMD penceresi 5 saniye sonra kapanacak.
timeout /t 5 /nobreak >nul
endlocal
exit /b 0
