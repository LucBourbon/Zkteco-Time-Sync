@echo off
rem Genera los .exe y arma release\ZKTeco-Time-Sync.zip listo para entregar.
rem Requiere Python de 32 bits con: pip install pyinstaller pywin32 PyQt5
cd /d "%~dp0"

python -c "import struct,sys; sys.exit(struct.calcsize('P')*8 != 32)" || (
    echo ERROR: Se necesita Python de 32 bits. La DLL de ZKTeco no funciona con 64 bits.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm ZKTeco_Sincronizador.spec || goto error
python -m PyInstaller --noconfirm SincronizarManual.spec || goto error

set "PKG=release\ZKTeco-Time-Sync"
if exist release rmdir /s /q release
mkdir "%PKG%\sdk" || goto error
copy /Y dist\ZKTeco_Sincronizador.exe "%PKG%\" || goto error
copy /Y dist\SincronizarManual.exe "%PKG%\" || goto error
copy /Y sdk\*.dll "%PKG%\sdk\" || goto error
copy /Y registrar_sdk.bat "%PKG%\" || goto error
copy /Y dispositivos.json "%PKG%\" || goto error
copy /Y README.md "%PKG%\" || goto error

powershell -NoProfile -Command "Compress-Archive -Path '%PKG%' -DestinationPath 'release\ZKTeco-Time-Sync.zip' -Force" || goto error

echo.
echo Listo: release\ZKTeco-Time-Sync.zip
pause
exit /b 0

:error
echo.
echo ERROR: Fallo el empaquetado.
pause
exit /b 1
