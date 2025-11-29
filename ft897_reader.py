#!/usr/bin/env python3
"""
FT-897 Radio Reader - GUI aplikace pro čtení a ovládání radiostanice Yaesu FT-897
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QMessageBox, QProgressBar, QStatusBar
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from ft897_cat import FT897


class FT897ReaderGUI(QMainWindow):
    """Hlavní okno aplikace pro čtení dat z FT-897"""

    def __init__(self):
        super().__init__()
        self.radio = None
        self.connected = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_radio_data)

        self.init_ui()

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        self.setWindowTitle('FT-897 Radio Reader')
        self.setGeometry(100, 100, 800, 600)

        # Hlavní widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Hlavní layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Sekce připojení
        connection_group = self.create_connection_group()
        main_layout.addWidget(connection_group)

        # Sekce zobrazení dat
        display_group = self.create_display_group()
        main_layout.addWidget(display_group)

        # Sekce ovládání
        control_group = self.create_control_group()
        main_layout.addWidget(control_group)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Nepřipojeno')

        # Nastavení stylů
        self.apply_styles()

    def create_connection_group(self) -> QGroupBox:
        """Vytvoří sekci pro připojení k radiostanici"""
        group = QGroupBox('Připojení k radiostanici')
        layout = QHBoxLayout()

        # Port
        layout.addWidget(QLabel('Port:'))
        self.port_input = QLineEdit('/dev/ttyUSB0')
        self.port_input.setPlaceholderText('např. /dev/ttyUSB0 nebo COM3')
        layout.addWidget(self.port_input)

        # Baudrate
        layout.addWidget(QLabel('Rychlost:'))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(['4800', '9600', '38400'])
        self.baudrate_combo.setCurrentText('4800')
        layout.addWidget(self.baudrate_combo)

        # Tlačítko připojení
        self.connect_button = QPushButton('Připojit')
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_display_group(self) -> QGroupBox:
        """Vytvoří sekci pro zobrazení dat z radiostanice"""
        group = QGroupBox('Aktuální stav radiostanice')
        layout = QGridLayout()

        # Frekvence
        layout.addWidget(QLabel('Frekvence:'), 0, 0)
        self.freq_label = QLabel('---')
        self.freq_label.setFont(QFont('Monospace', 24, QFont.Bold))
        self.freq_label.setStyleSheet('color: #00FF00; background-color: #000000; padding: 10px;')
        layout.addWidget(self.freq_label, 0, 1, 1, 3)

        # Mód
        layout.addWidget(QLabel('Mód:'), 1, 0)
        self.mode_label = QLabel('---')
        self.mode_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(self.mode_label, 1, 1)

        # S-meter
        layout.addWidget(QLabel('S-Meter:'), 2, 0)
        self.smeter_label = QLabel('---')
        self.smeter_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(self.smeter_label, 2, 1)

        self.smeter_bar = QProgressBar()
        self.smeter_bar.setMaximum(15)
        self.smeter_bar.setValue(0)
        self.smeter_bar.setTextVisible(False)
        layout.addWidget(self.smeter_bar, 2, 2, 1, 2)

        # Squelch
        layout.addWidget(QLabel('Squelch:'), 3, 0)
        self.squelch_label = QLabel('---')
        layout.addWidget(self.squelch_label, 3, 1)

        # CTCSS
        layout.addWidget(QLabel('CTCSS/DCS:'), 3, 2)
        self.ctcss_label = QLabel('---')
        layout.addWidget(self.ctcss_label, 3, 3)

        # TX Status
        layout.addWidget(QLabel('TX Status:'), 4, 0)
        self.tx_status_label = QLabel('RX')
        self.tx_status_label.setFont(QFont('Arial', 14, QFont.Bold))
        self.tx_status_label.setStyleSheet('color: green; padding: 5px;')
        layout.addWidget(self.tx_status_label, 4, 1)

        # Výkon
        layout.addWidget(QLabel('Výkon:'), 5, 0)
        self.power_label = QLabel('---')
        layout.addWidget(self.power_label, 5, 1)

        self.power_bar = QProgressBar()
        self.power_bar.setMaximum(100)
        self.power_bar.setValue(0)
        layout.addWidget(self.power_bar, 5, 2, 1, 2)

        # SWR
        layout.addWidget(QLabel('SWR:'), 6, 0)
        self.swr_label = QLabel('OK')
        self.swr_label.setStyleSheet('color: green;')
        layout.addWidget(self.swr_label, 6, 1)

        # Split
        layout.addWidget(QLabel('Split:'), 6, 2)
        self.split_label = QLabel('OFF')
        layout.addWidget(self.split_label, 6, 3)

        group.setLayout(layout)
        return group

    def create_control_group(self) -> QGroupBox:
        """Vytvoří sekci pro ovládání radiostanice"""
        group = QGroupBox('Ovládání')
        layout = QGridLayout()

        # Nastavení frekvence
        layout.addWidget(QLabel('Nastavit frekvenci (MHz):'), 0, 0)
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText('např. 14.250')
        layout.addWidget(self.freq_input, 0, 1)

        set_freq_button = QPushButton('Nastavit')
        set_freq_button.clicked.connect(self.set_frequency)
        layout.addWidget(set_freq_button, 0, 2)

        # VFO toggle
        vfo_button = QPushButton('Přepnout VFO A/B')
        vfo_button.clicked.connect(self.toggle_vfo)
        layout.addWidget(vfo_button, 1, 0)

        # Lock
        self.lock_button = QPushButton('Zamknout')
        self.lock_button.setCheckable(True)
        self.lock_button.clicked.connect(self.toggle_lock)
        layout.addWidget(self.lock_button, 1, 1)

        # Refresh rate
        layout.addWidget(QLabel('Frekvence aktualizace (ms):'), 2, 0)
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItems(['100', '250', '500', '1000', '2000'])
        self.refresh_combo.setCurrentText('500')
        self.refresh_combo.currentTextChanged.connect(self.change_refresh_rate)
        layout.addWidget(self.refresh_combo, 2, 1)

        group.setLayout(layout)
        return group

    def apply_styles(self):
        """Použije styly na aplikaci"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #888;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 3px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)

    def toggle_connection(self):
        """Připojí nebo odpojí radiostanici"""
        if not self.connected:
            # Připojení
            port = self.port_input.text()
            baudrate = int(self.baudrate_combo.currentText())

            self.radio = FT897(port=port, baudrate=baudrate)

            if self.radio.connect():
                self.connected = True
                self.connect_button.setText('Odpojit')
                self.connect_button.setStyleSheet('background-color: #f44336;')
                self.status_bar.showMessage(f'Připojeno k {port} @ {baudrate} baud')

                # Spustit timer pro aktualizaci dat
                refresh_ms = int(self.refresh_combo.currentText())
                self.update_timer.start(refresh_ms)

                # Povolit ovládací tlačítka
                self.enable_controls(True)

                # První aktualizace
                self.update_radio_data()
            else:
                QMessageBox.critical(
                    self,
                    'Chyba připojení',
                    f'Nelze se připojit k portu {port}.\n'
                    'Zkontrolujte, zda je radiostanice připojena a port je správný.'
                )
        else:
            # Odpojení
            self.update_timer.stop()
            if self.radio:
                self.radio.disconnect()

            self.connected = False
            self.connect_button.setText('Připojit')
            self.connect_button.setStyleSheet('background-color: #4CAF50;')
            self.status_bar.showMessage('Odpojeno')

            # Zakázat ovládací tlačítka
            self.enable_controls(False)

            # Vymazat zobrazení
            self.clear_display()

    def enable_controls(self, enabled: bool):
        """Povolí nebo zakáže ovládací prvky"""
        self.freq_input.setEnabled(enabled)
        self.lock_button.setEnabled(enabled)

    def clear_display(self):
        """Vymaže zobrazené údaje"""
        self.freq_label.setText('---')
        self.mode_label.setText('---')
        self.smeter_label.setText('---')
        self.smeter_bar.setValue(0)
        self.squelch_label.setText('---')
        self.ctcss_label.setText('---')
        self.tx_status_label.setText('RX')
        self.tx_status_label.setStyleSheet('color: green; padding: 5px;')
        self.power_label.setText('---')
        self.power_bar.setValue(0)
        self.swr_label.setText('OK')
        self.swr_label.setStyleSheet('color: green;')
        self.split_label.setText('OFF')

    def update_radio_data(self):
        """Aktualizuje data z radiostanice"""
        if not self.connected or not self.radio:
            return

        # Přečíst frekvenci a mód
        freq_mode = self.radio.get_frequency_and_mode()
        if freq_mode:
            freq_hz, mode = freq_mode
            freq_mhz = freq_hz / 1_000_000.0
            self.freq_label.setText(f'{freq_mhz:.6f} MHz')
            self.mode_label.setText(mode)

        # Přečíst RX status
        rx_status = self.radio.get_rx_status()
        if rx_status:
            self.smeter_label.setText(rx_status['s_meter'])
            self.smeter_bar.setValue(rx_status['s_meter_raw'])

            # Nastavit barvu S-metru podle síly signálu
            if rx_status['s_meter_raw'] >= 9:
                self.smeter_bar.setStyleSheet('QProgressBar::chunk { background-color: red; }')
            elif rx_status['s_meter_raw'] >= 5:
                self.smeter_bar.setStyleSheet('QProgressBar::chunk { background-color: yellow; }')
            else:
                self.smeter_bar.setStyleSheet('QProgressBar::chunk { background-color: green; }')

            squelch_text = 'OPEN' if rx_status['squelch_open'] else 'CLOSED'
            squelch_color = 'green' if rx_status['squelch_open'] else 'gray'
            self.squelch_label.setText(squelch_text)
            self.squelch_label.setStyleSheet(f'color: {squelch_color}; font-weight: bold;')

            ctcss_text = 'MATCH' if rx_status['ctcss_matched'] else 'NO MATCH'
            ctcss_color = 'green' if rx_status['ctcss_matched'] else 'gray'
            self.ctcss_label.setText(ctcss_text)
            self.ctcss_label.setStyleSheet(f'color: {ctcss_color};')

        # Přečíst TX status
        tx_status = self.radio.get_tx_status()
        if tx_status:
            if tx_status['ptt_active']:
                self.tx_status_label.setText('TX')
                self.tx_status_label.setStyleSheet('color: red; font-weight: bold; padding: 5px;')
            else:
                self.tx_status_label.setText('RX')
                self.tx_status_label.setStyleSheet('color: green; font-weight: bold; padding: 5px;')

            self.power_label.setText(f"{tx_status['power_percent']}%")
            self.power_bar.setValue(tx_status['power_percent'])

            if tx_status['high_swr']:
                self.swr_label.setText('HIGH!')
                self.swr_label.setStyleSheet('color: red; font-weight: bold;')
            else:
                self.swr_label.setText('OK')
                self.swr_label.setStyleSheet('color: green;')

            split_text = 'ON' if tx_status['split_active'] else 'OFF'
            split_color = 'orange' if tx_status['split_active'] else 'gray'
            self.split_label.setText(split_text)
            self.split_label.setStyleSheet(f'color: {split_color}; font-weight: bold;')

    def set_frequency(self):
        """Nastaví frekvenci radiostanice"""
        if not self.connected:
            return

        try:
            freq_mhz = float(self.freq_input.text())
            freq_hz = freq_mhz * 1_000_000.0

            if self.radio.set_frequency(freq_hz):
                self.status_bar.showMessage(f'Frekvence nastavena na {freq_mhz} MHz', 3000)
                # Okamžitá aktualizace
                self.update_radio_data()
            else:
                QMessageBox.warning(self, 'Chyba', 'Nelze nastavit frekvenci')

        except ValueError:
            QMessageBox.warning(
                self,
                'Neplatná frekvence',
                'Zadejte platnou frekvenci v MHz (např. 14.250)'
            )

    def toggle_vfo(self):
        """Přepne VFO A/B"""
        if not self.connected:
            return

        if self.radio.toggle_vfo():
            self.status_bar.showMessage('VFO přepnuto', 2000)
            # Okamžitá aktualizace
            self.update_radio_data()

    def toggle_lock(self):
        """Zamkne/odemkne frekvenční ovladač"""
        if not self.connected:
            return

        locked = self.lock_button.isChecked()

        if self.radio.set_lock(locked):
            if locked:
                self.lock_button.setText('Odemknout')
                self.lock_button.setStyleSheet('background-color: #ff9800;')
                self.status_bar.showMessage('Ovladač zamknut', 2000)
            else:
                self.lock_button.setText('Zamknout')
                self.lock_button.setStyleSheet('background-color: #4CAF50;')
                self.status_bar.showMessage('Ovladač odemknut', 2000)

    def change_refresh_rate(self, value: str):
        """Změní frekvenci aktualizace dat"""
        if self.connected:
            self.update_timer.stop()
            self.update_timer.start(int(value))
            self.status_bar.showMessage(f'Frekvence aktualizace změněna na {value} ms', 2000)

    def closeEvent(self, event):
        """Obsluha zavření okna"""
        if self.connected:
            self.update_timer.stop()
            if self.radio:
                self.radio.disconnect()
        event.accept()


def main():
    """Hlavní funkce aplikace"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Moderní vzhled

    window = FT897ReaderGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
