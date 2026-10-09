@echo off
rem Copia las DLL del SDK de ZKTeco (32 bits) a Windows y registra zkemkeeper.dll.
rem Ejecutar con clic derecho -> "Ejecutar como administrador".

net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ejecuta este archivo como Administrador.
    pause
    exit /b 1
)

if exist "%WINDIR%\SysWOW64" (set "DEST=%WINDIR%\SysWOW64") else (set "DEST=%WINDIR%\System32")

echo Copiando DLL a %DEST% ...
copy /Y "%~dp0sdk\*.dll" "%DEST%\" || goto error

echo Registrando zkemkeeper.dll ...
"%DEST%\regsvr32.exe" /s "%DEST%\zkemkeeper.dll" || goto error

echo.
echo Listo. SDK de ZKTeco registrado correctamente.
pause
exit /b 0

:error
echo.
echo ERROR: No se pudo instalar el SDK.
pause
exit /b 1
