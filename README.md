# FT-897 Radio Reader

Python aplikace s grafickým rozhraním Qt pro čtení a ovládání radiostanice **Yaesu FT-897** přes CAT protokol.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Funkce

### Zobrazení dat z radiostanice:
- ✅ **Aktuální frekvence** - velké zobrazení (36pt) s přesností na Hz
- ✅ **Provozní mód** - zvětšené zobrazení (24pt) (LSB, USB, CW, FM, AM, DIG, PKT)
- ✅ **S-Meter** (síla přijímaného signálu) s grafickým ukazatelem
- ✅ **Squelch status** (otevřený/zavřený)
- ✅ **CTCSS/DCS** detekce
- ✅ **TX/RX status** (vysílání/příjem)
- ✅ **Výkon vysílače** s procentuálním ukazatelem
- ✅ **SWR varování** (vysoký poměr stojatých vln)
- ✅ **Split mód** indikace

### Ovládání radiostanice:
- 🎛️ **Nastavení frekvence** - manuální nebo přes menu pásem
- 🔄 **Přepínání VFO A/B**
- 🔒 **Zamknutí frekvenčního ovladače**
- ⚡ **Nastavitelná frekvence aktualizace dat** (100ms - 2000ms)
- 📻 **Nastavení módu** přes menu (LSB, USB, CW, CW-R, AM, FM, DIG, PKT, FM-N)

### Pokročilé funkce:
- 🔌 **Automatická detekce COM portů** (Windows i Linux)
- 📡 **Radioamatérská pásma ČR** - rychlý přístup k běžným frekvencím (160m až 70cm)
- 💾 **Klonování pamětí** - vyčtení pamětí z radiostanice pomocí 0xBB EEPROM příkazu
- 💿 **Uložení/načtení clone souborů** - backup a obnovení konfigurace
- 📊 **Progress bar** při čtení pamětí

## Požadavky

### Hardware:
- Radiostanice **Yaesu FT-897** nebo **FT-897D**
- USB-sériový převodník nebo přímý sériový port
- CAT kabel pro připojení k radiostanici (připojení k zadnímu konektoru CAT/LINEAR)

### Software:
- Python 3.7 nebo novější
- PyQt5
- pyserial

## Instalace

### 1. Klonování repozitáře:
```bash
git clone <repository-url>
cd clone
```

### 2. Instalace závislostí:
```bash
pip install -r requirements.txt
```

Nebo manuálně:
```bash
pip install PyQt5 pyserial
```

### 3. Nastavení sériového portu (Linux):
Na Linuxu může být potřeba přidat uživatele do skupiny `dialout`:
```bash
sudo usermod -a -G dialout $USER
```
Poté se odhlaste a znovu přihlaste.

## Použití

### Spuštění aplikace:
```bash
python3 ft897_reader.py
```

### Připojení k radiostanici:

1. **Vyberte sériový port:**
   - Aplikace automaticky detekuje všechny dostupné COM porty
   - Vyberte port z rozbalovacího menu
   - Použijte tlačítko "🔄 Obnovit" pro aktualizaci seznamu portů

2. **Vyberte rychlost komunikace (baudrate):**
   - Výchozí: **4800** (nejběžnější nastavení FT-897)
   - Ostatní možnosti: 9600, 38400
   - Ujistěte se, že rychlost odpovídá nastavení v menu radiostanice

3. **Klikněte na "Připojit"**

### Použití menu funkcí:

#### Menu Pásma:
- Rychlý přístup k běžným frekvencím na radioamatérských pásmech v ČR
- Pásma: 160m, 80m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 6m, 2m, 70cm
- Kliknutím na frekvenci se radiostanice automaticky naladí

#### Menu Módy:
- Přepínání provozních módů: LSB, USB, CW, CW-R, AM, FM, DIG, PKT, FM-N
- Změna je okamžitá a zobrazí se na displeji

#### Menu Klonování:
- **Vyčíst paměti z radiostanice** - stáhne kompletní konfiguraci pomocí 0xBB příkazu
- Proces může trvat několik minut (čte se 8192 bajtů)
- Rychlost se automaticky přepne na 9600 baud
- Po dokončení použijte menu Soubor → Uložit pro zálohování

#### Menu Soubor:
- **Otevřít clone soubor** - načte dříve uloženou konfiguraci
- **Uložit clone soubor** - uloží vyčtenou konfiguraci do souboru (.ft897, .bin)

### Nastavení radiostanice FT-897:

Pro komunikaci s počítačem je třeba v radiostanici povolit CAT:

1. Stiskněte tlačítko **[FUNC]**
2. Otočte hlavním ovladačem na položku **CAT RATE**
3. Nastavte rychlost (4800, 9600 nebo 38400 baud)
4. Stiskněte **[FUNC]** pro uložení
5. Zapněte CAT: **FUNC** → **CAT** → **ON**

## Struktura projektu

```
.
├── ft897_cat.py         # CAT protokol - komunikační třída
├── ft897_reader.py      # Hlavní GUI aplikace
├── requirements.txt     # Python závislosti
└── README.md           # Tento soubor
```

## CAT Protokol

Aplikace implementuje **CAT (Computer Aided Transceiver)** protokol firmy Yaesu pro komunikaci s radiostanicí FT-897.

### Technické parametry:
- **Protokol:** 5-bajtové příkazy
- **Sériové nastavení:** 8N2 (8 datových bitů, bez parity, 2 stop bity)
- **Rychlost:** 4800, 9600 nebo 38400 baud
- **Konektor:** CAT/LINEAR (zadní panel FT-897)

### Implementované příkazy:

| Příkaz | Opcode | Popis |
|--------|--------|-------|
| Get Frequency/Mode | 0x03 | Čtení aktuální frekvence a módu |
| Get RX Status | 0xE7 | Čtení S-metru a squelch statusu |
| Get TX Status | 0xF7 | Čtení TX statusu, výkonu a SWR |
| Set Frequency | 0x01 | Nastavení provozní frekvence |
| Set Mode | 0x07 | Nastavení provozního módu |
| Toggle VFO | 0x81 | Přepnutí mezi VFO A a B |
| Lock ON/OFF | 0x00/0x80 | Zamknutí/odemknutí frekv. ovladače |
| **Read EEPROM** | **0xBB** | **Čtení 2 bajtů z EEPROM (klonování)** |

**Nově přidáno:** Příkaz 0xBB umožňuje čtení kompletní paměti radiostanice (8192 bajtů) pro zálohování konfigurace.

Kompletní dokumentaci CAT protokolu najdete v oficiálním manuálu FT-897.

## Řešení problémů

### Aplikace se nemůže připojit k radiostanici:

1. **Zkontrolujte sériový port:**
   ```bash
   # Linux - seznam portů
   ls -l /dev/ttyUSB* /dev/ttyACM*

   # Windows - Device Manager
   # Kontrola v "Porty (COM a LPT)"
   ```

2. **Zkontrolujte oprávnění (Linux):**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   # nebo
   sudo usermod -a -G dialout $USER
   ```

3. **Ověřte nastavení CAT v radiostanici:**
   - CAT musí být zapnutý (CAT = ON)
   - Rychlost (CAT RATE) musí odpovídat nastavení v aplikaci
   - Kabel musí být správně zapojen do konektoru CAT/LINEAR

4. **Zkontrolujte kabel:**
   - Některé USB-sériové převodníky vyžadují speciální ovladače
   - Použijte kvalitní USB kabel
   - Zkuste jiný USB port

### Data se neaktualizují:

1. Zkontrolujte, zda je radiostanice zapnutá
2. Zkuste zvýšit frekvenci aktualizace (interval refresh)
3. Restartujte aplikaci a radiostanici

### Nesprávné hodnoty S-metru:

- S-meter se aktualizuje pouze při otevřeném squelchi a přítomnosti signálu
- Některé módy mohou vykazovat nepřesné hodnoty
- Zkuste přepnout na jiný mód nebo VFO

## Příklady použití

### Monitorování radiostanice:
```python
from ft897_cat import FT897

# Vytvoření instance
radio = FT897(port='/dev/ttyUSB0', baudrate=4800)

# Připojení
if radio.connect():
    # Čtení frekvence a módu
    freq, mode = radio.get_frequency_and_mode()
    print(f"Frekvence: {freq/1e6:.6f} MHz, Mód: {mode}")

    # Čtení RX statusu
    rx_status = radio.get_rx_status()
    print(f"S-Meter: {rx_status['s_meter']}")

    # Odpojení
    radio.disconnect()
```

### Nastavení frekvence:
```python
# Nastavení na 14.250 MHz (20m pásmo)
radio.set_frequency(14_250_000)
```

## Zdrojové informace

Aplikace byla vytvořena na základě oficiální dokumentace:
- [FT-897D CAT Commands (Yaesu Official)](https://www.qsl.net/sp9hzx/pdf/FT-897D_Yaesu-official_CAT-Commands.pdf)
- [FT-897 Operating Manual - CAT Operation](https://www.manualslib.com/manual/1064483/Yaesu-Ft-897.html?page=63)
- [Hamlib FT-897 Implementation](https://github.com/jkjuopperi/hamlib/blob/master/yaesu/ft897.c)

## Licence

MIT License - volně použitelné pro osobní i komerční účely.

## Autor

Vytvořeno pomocí AI asistenta Claude s využitím PyQt5 a PySerial knihoven.

## Přispění

Příspěvky jsou vítány! Neváhejte vytvořit issue nebo pull request.

---

**73!** 📻
*Šťastné DXování s FT-897!*
