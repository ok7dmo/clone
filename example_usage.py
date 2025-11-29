#!/usr/bin/env python3
"""
Příklad použití FT-897 CAT knihovny bez GUI
Jednoduchý skript pro testování komunikace s radiostanicí
"""

import time
from ft897_cat import FT897


def main():
    """Hlavní funkce - demonstrace použití CAT knihovny"""

    # Nastavení portu a rychlosti
    # Linux: '/dev/ttyUSB0', Windows: 'COM3'
    PORT = '/dev/ttyUSB0'
    BAUDRATE = 4800

    print("=" * 60)
    print("FT-897 CAT Protokol - Příklad použití")
    print("=" * 60)

    # Vytvoření instance radiostanice
    radio = FT897(port=PORT, baudrate=BAUDRATE)

    # Pokus o připojení
    print(f"\nPřipojuji se k {PORT} @ {BAUDRATE} baud...")

    if not radio.connect():
        print("❌ Nepodařilo se připojit k radiostanici!")
        print("\nZkontrolujte:")
        print("  - Je radiostanice zapnutá?")
        print("  - Je CAT protokol povolen v menu radiostanice?")
        print("  - Je správně nastavena rychlost (CAT RATE)?")
        print("  - Je kabel správně připojen?")
        print(f"  - Je port {PORT} správný?")
        return

    print("✅ Připojeno k radiostanici FT-897!")

    try:
        # Čekání na stabilizaci spojení
        time.sleep(0.2)

        # 1. Čtení frekvence a módu
        print("\n" + "-" * 60)
        print("📡 Čtení aktuální frekvence a módu...")
        print("-" * 60)

        result = radio.get_frequency_and_mode()
        if result:
            freq_hz, mode = result
            freq_mhz = freq_hz / 1_000_000.0
            print(f"  Frekvence: {freq_mhz:.6f} MHz")
            print(f"  Mód:       {mode}")
        else:
            print("  ❌ Nelze přečíst frekvenci")

        # 2. Čtení RX statusu
        print("\n" + "-" * 60)
        print("📊 Čtení RX statusu...")
        print("-" * 60)

        rx_status = radio.get_rx_status()
        if rx_status:
            print(f"  S-Meter:        {rx_status['s_meter']} (raw: {rx_status['s_meter_raw']})")
            print(f"  Squelch:        {'OPEN ✅' if rx_status['squelch_open'] else 'CLOSED'}")
            print(f"  CTCSS/DCS:      {'MATCH ✅' if rx_status['ctcss_matched'] else 'NO MATCH'}")
            print(f"  Disc. Centered: {'YES' if rx_status['disc_centered'] else 'NO'}")
        else:
            print("  ❌ Nelze přečíst RX status")

        # 3. Čtení TX statusu
        print("\n" + "-" * 60)
        print("📶 Čtení TX statusu...")
        print("-" * 60)

        tx_status = radio.get_tx_status()
        if tx_status:
            print(f"  PTT:       {'TX 🔴' if tx_status['ptt_active'] else 'RX 🟢'}")
            print(f"  Výkon:     {tx_status['power_percent']}% (raw: {tx_status['power_raw']})")
            print(f"  SWR:       {'HIGH ⚠️' if tx_status['high_swr'] else 'OK ✅'}")
            print(f"  Split:     {'ON' if tx_status['split_active'] else 'OFF'}")
        else:
            print("  ❌ Nelze přečíst TX status")

        # 4. Demonstrace nastavení frekvence
        print("\n" + "-" * 60)
        print("🎛️  Test nastavení frekvence...")
        print("-" * 60)

        # Uložit původní frekvenci
        original_freq = None
        result = radio.get_frequency_and_mode()
        if result:
            original_freq, _ = result

        # Nastavit testovací frekvenci (14.250 MHz - 20m pásmo)
        test_freq = 14_250_000  # Hz
        print(f"  Nastavuji frekvenci na {test_freq/1e6:.6f} MHz...")

        if radio.set_frequency(test_freq):
            print("  ✅ Frekvence nastavena")
            time.sleep(0.5)

            # Ověření
            result = radio.get_frequency_and_mode()
            if result:
                new_freq, mode = result
                print(f"  Ověření: {new_freq/1e6:.6f} MHz, {mode}")
        else:
            print("  ❌ Nelze nastavit frekvenci")

        # Vrátit původní frekvenci
        if original_freq:
            print(f"\n  Vracím původní frekvenci {original_freq/1e6:.6f} MHz...")
            radio.set_frequency(original_freq)
            time.sleep(0.2)

        # 5. Test VFO přepínání
        print("\n" + "-" * 60)
        print("🔄 Test přepínání VFO...")
        print("-" * 60)

        result = radio.get_frequency_and_mode()
        if result:
            vfo_a_freq, vfo_a_mode = result
            print(f"  VFO A: {vfo_a_freq/1e6:.6f} MHz, {vfo_a_mode}")

        print("  Přepínám na VFO B...")
        if radio.toggle_vfo():
            time.sleep(0.3)
            result = radio.get_frequency_and_mode()
            if result:
                vfo_b_freq, vfo_b_mode = result
                print(f"  VFO B: {vfo_b_freq/1e6:.6f} MHz, {vfo_b_mode}")

            print("  Přepínám zpět na VFO A...")
            radio.toggle_vfo()
            time.sleep(0.3)

        # 6. Kontinuální monitorování (5 sekund)
        print("\n" + "-" * 60)
        print("🔍 Kontinuální monitorování (5 sekund)...")
        print("-" * 60)
        print("\nFrekvence      | Mód  | S-Meter | Squelch | TX")
        print("-" * 60)

        start_time = time.time()
        while time.time() - start_time < 5:
            freq_mode = radio.get_frequency_and_mode()
            rx_status = radio.get_rx_status()
            tx_status = radio.get_tx_status()

            if freq_mode and rx_status and tx_status:
                freq_hz, mode = freq_mode
                freq_mhz = freq_hz / 1_000_000.0
                squelch = "OPEN" if rx_status['squelch_open'] else "CLSD"
                tx_rx = "TX" if tx_status['ptt_active'] else "RX"

                print(f"\r{freq_mhz:12.6f} | {mode:4} | {rx_status['s_meter']:7} | {squelch:7} | {tx_rx:2}", end='', flush=True)

            time.sleep(0.5)

        print("\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Přerušeno uživatelem")

    except Exception as e:
        print(f"\n❌ Chyba: {e}")

    finally:
        # Odpojení
        print("\n" + "=" * 60)
        print("Odpojuji se od radiostanice...")
        radio.disconnect()
        print("✅ Odpojeno")
        print("=" * 60)


if __name__ == '__main__':
    main()
