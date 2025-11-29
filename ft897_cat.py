"""
FT-897 CAT (Computer Aided Transceiver) Protocol Implementation
Komunikace s radiostanicí Yaesu FT-897 přes sériový port
"""

import serial
import time
from typing import Optional, Tuple


class FT897:
    """Třída pro komunikaci s radiostanicí Yaesu FT-897 pomocí CAT protokolu"""

    # CAT Command Opcodes
    CMD_LOCK_ON = 0x00
    CMD_LOCK_OFF = 0x80
    CMD_PTT_ON = 0x08
    CMD_PTT_OFF = 0x88
    CMD_SET_FREQ = 0x01
    CMD_MODE_SET = 0x07
    CMD_CLAR_ON = 0x05
    CMD_CLAR_OFF = 0x85
    CMD_VFO_AB = 0x81
    CMD_SPLIT_ON = 0x02
    CMD_SPLIT_OFF = 0x82
    CMD_SET_RPT_SHIFT = 0x09
    CMD_SET_CTCSS_TONE = 0x0A
    CMD_SET_DCS_CODE = 0x0B
    CMD_CTCSS_ON = 0x2A
    CMD_CTCSS_OFF = 0x8A
    CMD_DCS_ON = 0x2B
    CMD_DCS_OFF = 0x8B

    # Read Commands
    CMD_GET_FREQ_MODE = 0x03
    CMD_GET_RX_STATUS = 0xE7
    CMD_GET_TX_STATUS = 0xF7
    CMD_READ_TX_METERING = 0xBD
    CMD_READ_RX_STATUS_FLAGS = 0xFA

    # Modes
    MODES = {
        0x00: 'LSB',
        0x01: 'USB',
        0x02: 'CW',
        0x03: 'CW-R',
        0x04: 'AM',
        0x05: 'FM',
        0x06: 'DIG',
        0x08: 'PKT',
        0x0A: 'FM-N',
        0x0C: 'DIG',
        0x82: 'CW',
        0x83: 'CW-R',
        0x84: 'AM',
        0x88: 'PKT'
    }

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 4800, timeout: float = 0.5):
        """
        Inicializace komunikace s FT-897

        Args:
            port: Sériový port (např. '/dev/ttyUSB0' nebo 'COM3')
            baudrate: Rychlost komunikace (4800, 9600, nebo 38400)
            timeout: Timeout pro čtení v sekundách
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

    def connect(self) -> bool:
        """
        Připojení k radiostanici

        Returns:
            True pokud se připojení zdařilo, jinak False
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,  # FT-897 používá 2 stop bity
                timeout=self.timeout
            )
            time.sleep(0.1)  # Krátké čekání po otevření portu
            # Vyčistit buffer
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            return True
        except Exception as e:
            print(f"Chyba při připojení: {e}")
            return False

    def disconnect(self):
        """Odpojení od radiostanice"""
        if self.serial and self.serial.is_open:
            self.serial.close()

    def _send_command(self, cmd_bytes: bytes) -> bool:
        """
        Odeslání CAT příkazu

        Args:
            cmd_bytes: 5-bajtový příkaz

        Returns:
            True pokud se odeslání zdařilo
        """
        if not self.serial or not self.serial.is_open:
            return False

        try:
            self.serial.write(cmd_bytes)
            self.serial.flush()
            return True
        except Exception as e:
            print(f"Chyba při odesílání příkazu: {e}")
            return False

    def _read_response(self, length: int) -> Optional[bytes]:
        """
        Přečtení odpovědi z radiostanice

        Args:
            length: Počet bajtů k přečtení

        Returns:
            Přečtené bajty nebo None při chybě
        """
        if not self.serial or not self.serial.is_open:
            return None

        try:
            data = self.serial.read(length)
            if len(data) == length:
                return data
            return None
        except Exception as e:
            print(f"Chyba při čtení odpovědi: {e}")
            return None

    def get_frequency_and_mode(self) -> Optional[Tuple[float, str]]:
        """
        Přečte aktuální frekvenci a mód

        Returns:
            Tuple (frekvence_v_Hz, mód) nebo None při chybě
        """
        cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_GET_FREQ_MODE])

        if not self._send_command(cmd):
            return None

        response = self._read_response(5)
        if not response:
            return None

        # Dekódování BCD frekvence (8 číslic)
        freq_str = ""
        for i in range(4):
            high_nibble = (response[i] >> 4) & 0x0F
            low_nibble = response[i] & 0x0F
            freq_str += str(high_nibble) + str(low_nibble)

        frequency = int(freq_str) / 100.0  # Frekvence je v 10 Hz, převod na Hz

        # Dekódování módu
        mode_byte = response[4]
        mode = self.MODES.get(mode_byte, f'Unknown (0x{mode_byte:02X})')

        return (frequency, mode)

    def get_rx_status(self) -> Optional[dict]:
        """
        Přečte RX status (S-meter, squelch, atd.)

        Returns:
            Slovník s hodnotami nebo None při chybě
        """
        cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_GET_RX_STATUS])

        if not self._send_command(cmd):
            return None

        response = self._read_response(1)
        if not response:
            return None

        status_byte = response[0]

        # Bit 7: Squelch status (1 = squelch open, carrier detected)
        squelch_open = bool(status_byte & 0x80)

        # Bit 6: CTCSS/DCS code matched
        ctcss_matched = bool(status_byte & 0x40)

        # Bit 5: Discriminator centered (FM mode)
        disc_centered = bool(status_byte & 0x20)

        # Bits 3-0: S-meter reading (0-15)
        s_meter_raw = status_byte & 0x0F

        # Převod S-meter hodnoty na S jednotky a dB
        if s_meter_raw == 0:
            s_meter = "S0"
        elif s_meter_raw <= 9:
            s_meter = f"S{s_meter_raw}"
        else:
            db_over_s9 = (s_meter_raw - 9) * 10
            s_meter = f"S9+{db_over_s9}dB"

        return {
            'squelch_open': squelch_open,
            'ctcss_matched': ctcss_matched,
            'disc_centered': disc_centered,
            's_meter_raw': s_meter_raw,
            's_meter': s_meter
        }

    def get_tx_status(self) -> Optional[dict]:
        """
        Přečte TX status (PTT, výkon, SWR)

        Returns:
            Slovník s hodnotami nebo None při chybě
        """
        cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_GET_TX_STATUS])

        if not self._send_command(cmd):
            return None

        response = self._read_response(1)
        if not response:
            return None

        status_byte = response[0]

        # Bit 7: PTT status (1 = transmitting)
        ptt_active = bool(status_byte & 0x80)

        # Bit 6: High SWR detected
        high_swr = bool(status_byte & 0x40)

        # Bit 5: Split mode active
        split_active = bool(status_byte & 0x20)

        # Bits 3-0: Power meter reading (0-15)
        power_raw = status_byte & 0x0F

        # Převod na procenta (přibližně)
        power_percent = int((power_raw / 15.0) * 100)

        return {
            'ptt_active': ptt_active,
            'high_swr': high_swr,
            'split_active': split_active,
            'power_raw': power_raw,
            'power_percent': power_percent
        }

    def set_frequency(self, freq_hz: float) -> bool:
        """
        Nastaví frekvenci

        Args:
            freq_hz: Frekvence v Hz

        Returns:
            True pokud se nastavení zdařilo
        """
        # Převod frekvence na BCD formát (8 číslic, v 10 Hz)
        freq_10hz = int(freq_hz / 10.0)
        freq_str = f"{freq_10hz:08d}"

        # Konverze na BCD bajty
        bcd_bytes = []
        for i in range(0, 8, 2):
            high = int(freq_str[i])
            low = int(freq_str[i + 1])
            bcd_bytes.append((high << 4) | low)

        cmd = bytes(bcd_bytes + [self.CMD_SET_FREQ])
        return self._send_command(cmd)

    def set_ptt(self, on: bool) -> bool:
        """
        Zapne/vypne PTT (vysílání)

        Args:
            on: True pro zapnutí vysílání, False pro vypnutí

        Returns:
            True pokud se příkaz odeslal úspěšně
        """
        if on:
            cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_PTT_ON])
        else:
            cmd = bytes([0x00, 0x00, 0x00, 0x01, self.CMD_PTT_OFF])

        return self._send_command(cmd)

    def toggle_vfo(self) -> bool:
        """Přepne mezi VFO A a B"""
        cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_VFO_AB])
        return self._send_command(cmd)

    def set_lock(self, on: bool) -> bool:
        """
        Zamkne/odemkne frekvenční ovladač

        Args:
            on: True pro zamknutí, False pro odemknutí
        """
        if on:
            cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_LOCK_ON])
        else:
            cmd = bytes([0x00, 0x00, 0x00, 0x00, self.CMD_LOCK_OFF])

        return self._send_command(cmd)
