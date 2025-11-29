#!/bin/bash
# Spouštěcí skript pro Linux/macOS

echo "========================================="
echo "FT-897 Radio Reader - Spouštění"
echo "========================================="
echo ""

# Kontrola Python verze
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 není nainstalován!"
    echo "Nainstalujte Python 3.7 nebo novější"
    exit 1
fi

echo "✅ Python verze: $(python3 --version)"

# Kontrola závislostí
echo ""
echo "Kontroluji závislosti..."

if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "❌ PyQt5 není nainstalován!"
    echo "Spouštím instalaci závislostí..."
    pip3 install -r requirements.txt
else
    echo "✅ PyQt5 je nainstalován"
fi

if ! python3 -c "import serial" 2>/dev/null; then
    echo "❌ pyserial není nainstalován!"
    echo "Spouštím instalaci závislostí..."
    pip3 install -r requirements.txt
else
    echo "✅ pyserial je nainstalován"
fi

# Kontrola oprávnění k sériovému portu
echo ""
echo "Kontroluji oprávnění k sériovému portu..."
if groups | grep -q dialout; then
    echo "✅ Uživatel má oprávnění k sériovému portu (dialout)"
else
    echo "⚠️  Uživatel není ve skupině 'dialout'"
    echo "   Pro přidání spusťte: sudo usermod -a -G dialout $USER"
    echo "   Poté se odhlaste a znovu přihlaste"
fi

# Spuštění aplikace
echo ""
echo "========================================="
echo "Spouštím FT-897 Radio Reader..."
echo "========================================="
echo ""

python3 ft897_reader.py
