#!/usr/bin/env python3
"""
Diagnostický skript pro testování připojení k FT-897
Pomáhá identifikovat problémy se sériovým portem a komunikací
"""

import sys
import serial
import serial.tools.list_ports
from ft897_cat import FT897


def list_serial_ports():
    """Vypíše všechny dostupné sériové porty"""
    print("\n" + "=" * 60)
    print("DOSTUPNÉ SÉRIOVÉ PORTY")
    print("=" * 60)

    ports = serial.tools.list_ports.comports()

    if not ports:
        print("❌ Nenalezeny žádné sériové porty!")
        print("\nMožné příčiny:")
        print("  - USB-sériový převodník není připojen")
        print("  - Chybí ovladač pro převodník")
        print("  - Problémy s USB kabelem")
        return None

    print(f"\nNalezeno {len(ports)} portů:\n")

    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Popis:      {port.description}")
        print(f"   Výrobce:    {port.manufacturer or 'N/A'}")
        print(f"   VID:PID:    {port.vid:04X}:{port.pid:04X}" if port.vid else "   VID:PID:    N/A")
        print(f"   Sériové č.: {port.serial_number or 'N/A'}")
        print()

    return [port.device for port in ports]


def test_port_access(port_name):
    """Testuje, zda lze otevřít sériový port"""
    print("\n" + "=" * 60)
    print(f"TEST PŘÍSTUPU K PORTU: {port_name}")
    print("=" * 60)

    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=4800,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=0.5
        )
        ser.close()
        print(f"✅ Port {port_name} lze otevřít")
        return True

    except serial.SerialException as e:
        print(f"❌ Nelze otevřít port {port_name}")
        print(f"   Chyba: {e}")
        print("\nMožná řešení:")
        print("  - Linux: sudo chmod 666 " + port_name)
        print("  - Linux: sudo usermod -a -G dialout $USER (pak se odhlaste)")
        print("  - Windows: Zkontrolujte Device Manager")
        print("  - Zkuste jiný USB port")
        print("  - Restartujte počítač")
        return False

    except Exception as e:
        print(f"❌ Neočekávaná chyba: {e}")
        return False


def test_cat_communication(port_name, baudrate=4800):
    """Testuje CAT komunikaci s FT-897"""
    print("\n" + "=" * 60)
    print(f"TEST CAT KOMUNIKACE: {port_name} @ {baudrate} baud")
    print("=" * 60)

    radio = FT897(port=port_name, baudrate=baudrate)

    print(f"\nPřipojuji se k {port_name}...")

    if not radio.connect():
        print("❌ Nepodařilo se připojit!")
        print("\nMožné příčiny:")
        print("  - Radiostanice není zapnutá")
        print("  - CAT protokol není povolen v radiostanici")
        print("  - Špatně nastavená rychlost (CAT RATE)")
        print("  - Problém s CAT kabelem")
        print("  - Špatný port")
        return False

    print("✅ Připojeno!")

    # Test 1: Čtení frekvence a módu
    print("\nTest 1: Čtení frekvence a módu...")
    result = radio.get_frequency_and_mode()

    if result:
        freq_hz, mode = result
        freq_mhz = freq_hz / 1_000_000.0
        print(f"  ✅ Úspěch!")
        print(f"     Frekvence: {freq_mhz:.6f} MHz")
        print(f"     Mód:       {mode}")
    else:
        print("  ❌ Nepodařilo se přečíst frekvenci")
        print("     Možná je potřeba delší timeout")

    # Test 2: Čtení RX statusu
    print("\nTest 2: Čtení RX statusu...")
    rx_status = radio.get_rx_status()

    if rx_status:
        print(f"  ✅ Úspěch!")
        print(f"     S-Meter: {rx_status['s_meter']}")
        print(f"     Squelch: {'OPEN' if rx_status['squelch_open'] else 'CLOSED'}")
    else:
        print("  ❌ Nepodařilo se přečíst RX status")

    # Test 3: Čtení TX statusu
    print("\nTest 3: Čtení TX statusu...")
    tx_status = radio.get_tx_status()

    if tx_status:
        print(f"  ✅ Úspěch!")
        print(f"     PTT:   {'TX' if tx_status['ptt_active'] else 'RX'}")
        print(f"     Výkon: {tx_status['power_percent']}%")
    else:
        print("  ❌ Nepodařilo se přečíst TX status")

    # Odpojení
    radio.disconnect()
    print("\n✅ Test dokončen, odpojeno")

    return True


def interactive_test():
    """Interaktivní test s volbou portu"""
    print("\n" + "=" * 60)
    print("FT-897 DIAGNOSTICKÝ NÁSTROJ")
    print("=" * 60)

    # Seznam portů
    ports = list_serial_ports()

    if not ports:
        return

    # Výběr portu
    print("\nVyberte port pro test:")
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port}")
    print(f"  {len(ports) + 1}. Zadat vlastní port")
    print("  0. Ukončit")

    try:
        choice = int(input("\nVaše volba: "))

        if choice == 0:
            print("Ukončuji...")
            return

        if choice == len(ports) + 1:
            port_name = input("Zadejte název portu (např. /dev/ttyUSB0 nebo COM3): ")
        elif 1 <= choice <= len(ports):
            port_name = ports[choice - 1]
        else:
            print("❌ Neplatná volba!")
            return

    except ValueError:
        print("❌ Neplatný vstup!")
        return

    # Test přístupu k portu
    if not test_port_access(port_name):
        return

    # Výběr rychlosti
    print("\nVyberte rychlost komunikace:")
    print("  1. 4800 baud (výchozí)")
    print("  2. 9600 baud")
    print("  3. 38400 baud")

    try:
        baud_choice = int(input("\nVaše volba (1-3): ") or "1")
        baudrates = {1: 4800, 2: 9600, 3: 38400}
        baudrate = baudrates.get(baud_choice, 4800)
    except ValueError:
        baudrate = 4800

    # Test CAT komunikace
    test_cat_communication(port_name, baudrate)

    print("\n" + "=" * 60)
    print("DIAGNOSTIKA DOKONČENA")
    print("=" * 60)


def main():
    """Hlavní funkce"""
    if len(sys.argv) > 1:
        # Režim s parametry
        port_name = sys.argv[1]
        baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 4800

        test_port_access(port_name)
        test_cat_communication(port_name, baudrate)
    else:
        # Interaktivní režim
        interactive_test()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Přerušeno uživatelem")
        sys.exit(0)
