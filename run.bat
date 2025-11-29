@echo off
REM Spouštěcí skript pro Windows

echo =========================================
echo FT-897 Radio Reader - Spouštění
echo =========================================
echo.

REM Kontrola Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python není nainstalován!
    echo Stáhněte a nainstalujte Python z https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python je nainstalován
python --version

REM Kontrola závislostí
echo.
echo Kontroluji závislosti...

python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo ❌ PyQt5 není nainstalován!
    echo Spouštím instalaci závislostí...
    pip install -r requirements.txt
) else (
    echo ✅ PyQt5 je nainstalován
)

python -c "import serial" 2>nul
if errorlevel 1 (
    echo ❌ pyserial není nainstalován!
    echo Spouštím instalaci závislostí...
    pip install -r requirements.txt
) else (
    echo ✅ pyserial je nainstalován
)

REM Spuštění aplikace
echo.
echo =========================================
echo Spouštím FT-897 Radio Reader...
echo =========================================
echo.

python ft897_reader.py

pause
