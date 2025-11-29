#!/usr/bin/env python3
"""
FT-897 Radio Reader - GUI aplikace pro čtení a ovládání radiostanice Yaesu FT-897
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QMessageBox, QProgressBar, QStatusBar, QMenuBar,
    QMenu, QAction, QFileDialog, QDialog, QDialogButtonBox, QTextEdit
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
        self.setWindowTitle('FT-897 Radio Reader & Controller')
        self.setGeometry(100, 100, 900, 700)

        # Menu bar
        self.create_menu_bar()

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

    def create_menu_bar(self):
        """Vytvoří menu bar s nabídkami"""
        menubar = self.menuBar()

        # Menu Soubor
        file_menu = menubar.addMenu('&Soubor')

        open_clone_action = QAction('Otevřít clone soubor...', self)
        open_clone_action.triggered.connect(self.open_clone_file)
        file_menu.addAction(open_clone_action)

        save_clone_action = QAction('Uložit clone soubor...', self)
        save_clone_action.triggered.connect(self.save_clone_file)
        file_menu.addAction(save_clone_action)

        file_menu.addSeparator()

        exit_action = QAction('&Konec', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Klonování
        clone_menu = menubar.addMenu('&Klonování')

        read_memory_action = QAction('Vyčíst paměti z radiostanice...', self)
        read_memory_action.triggered.connect(self.read_memories)
        clone_menu.addAction(read_memory_action)

        # Menu Módy
        modes_menu = menubar.addMenu('&Módy')
        mode_list = ['LSB', 'USB', 'CW', 'CW-R', 'AM', 'FM', 'DIG', 'PKT', 'FM-N']
        for mode in mode_list:
            mode_action = QAction(mode, self)
            mode_action.triggered.connect(lambda checked, m=mode: self.set_mode(m))
            modes_menu.addAction(mode_action)

        # Menu Pásma
        bands_menu = menubar.addMenu('&Pásma')
        self.create_bands_menu(bands_menu)

        # Menu Nápověda
        help_menu = menubar.addMenu('&Nápověda')

        about_action = QAction('O aplikaci...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_bands_menu(self, parent_menu):
        """Vytvoří podnabídky pro radioamatérská pásma ČR"""

        # Definice pásem a frekvencí pro ČR
        bands = {
            '160m (1.8-2.0 MHz)': [
                ('1.850 MHz (CW)', 1.850),
                ('1.890 MHz (SSB)', 1.890),
            ],
            '80m (3.5-3.8 MHz)': [
                ('3.650 MHz (CW/Digital)', 3.650),
                ('3.700 MHz (SSB)', 3.700),
                ('3.775 MHz (SSB)', 3.775),
            ],
            '40m (7.0-7.2 MHz)': [
                ('7.050 MHz (CW/Digital)', 7.050),
                ('7.100 MHz (SSB)', 7.100),
                ('7.130 MHz (SSB)', 7.130),
            ],
            '30m (10.1-10.15 MHz)': [
                ('10.130 MHz (CW/Digital)', 10.130),
                ('10.140 MHz (Digital)', 10.140),
            ],
            '20m (14.0-14.35 MHz)': [
                ('14.100 MHz (CW/Digital)', 14.100),
                ('14.200 MHz (SSB)', 14.200),
                ('14.250 MHz (SSB)', 14.250),
            ],
            '17m (18.068-18.168 MHz)': [
                ('18.100 MHz (CW/Digital)', 18.100),
                ('18.130 MHz (SSB)', 18.130),
            ],
            '15m (21.0-21.45 MHz)': [
                ('21.150 MHz (CW/Digital)', 21.150),
                ('21.250 MHz (SSB)', 21.250),
                ('21.300 MHz (SSB)', 21.300),
            ],
            '12m (24.89-24.99 MHz)': [
                ('24.930 MHz (CW/Digital)', 24.930),
                ('24.950 MHz (SSB)', 24.950),
            ],
            '10m (28.0-29.7 MHz)': [
                ('28.500 MHz (CW/Digital)', 28.500),
                ('29.000 MHz (FM)', 29.000),
                ('29.600 MHz (FM)', 29.600),
            ],
            '6m (50.0-52.0 MHz)': [
                ('50.100 MHz (SSB)', 50.100),
                ('50.200 MHz (SSB)', 50.200),
                ('51.000 MHz (FM)', 51.000),
            ],
            '2m (144-146 MHz)': [
                ('144.500 MHz (SSB)', 144.500),
                ('145.200 MHz (FM)', 145.200),
                ('145.500 MHz (FM)', 145.500),
            ],
            '70cm (430-440 MHz)': [
                ('432.500 MHz (SSB)', 432.500),
                ('433.500 MHz (FM)', 433.500),
                ('435.000 MHz (FM)', 435.000),
            ],
        }

        for band_name, frequencies in bands.items():
            band_menu = parent_menu.addMenu(band_name)
            for freq_name, freq_mhz in frequencies:
                freq_action = QAction(freq_name, self)
                freq_action.triggered.connect(
                    lambda checked, f=freq_mhz: self.set_frequency_from_menu(f)
                )
                band_menu.addAction(freq_action)

    def create_connection_group(self) -> QGroupBox:
        """Vytvoří sekci pro připojení k radiostanici"""
        group = QGroupBox('Připojení k radiostanici')
        layout = QHBoxLayout()

        # Port - nyní jako ComboBox s automatickou detekcí portů
        layout.addWidget(QLabel('Port:'))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self.refresh_ports()
        layout.addWidget(self.port_combo)

        # Tlačítko pro refresh portů
        refresh_button = QPushButton('🔄 Obnovit')
        refresh_button.clicked.connect(self.refresh_ports)
        refresh_button.setMaximumWidth(80)
        layout.addWidget(refresh_button)

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

    def refresh_ports(self):
        """Obnoví seznam dostupných portů"""
        self.port_combo.clear()
        ports = FT897.list_available_ports()

        if not ports:
            self.port_combo.addItem("Žádné porty nenalezeny")
        else:
            for port_name, port_desc in ports:
                self.port_combo.addItem(port_desc, port_name)

    def create_display_group(self) -> QGroupBox:
        """Vytvoří sekci pro zobrazení dat z radiostanice"""
        group = QGroupBox('Aktuální stav radiostanice')
        layout = QGridLayout()

        # Frekvence - VELKÉ zobrazení
        layout.addWidget(QLabel('Frekvence:'), 0, 0)
        self.freq_label = QLabel('---')
        self.freq_label.setFont(QFont('Monospace', 36, QFont.Bold))
        self.freq_label.setStyleSheet('color: #00FF00; background-color: #000000; padding: 15px; border: 2px solid #00FF00;')
        self.freq_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.freq_label, 0, 1, 1, 3)

        # Mód - větší zobrazení
        layout.addWidget(QLabel('Mód:'), 1, 0)
        self.mode_label = QLabel('---')
        self.mode_label.setFont(QFont('Arial', 24, QFont.Bold))
        self.mode_label.setStyleSheet('color: #0099FF; padding: 5px;')
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
            port = self.port_combo.currentData()
            if not port:
                QMessageBox.warning(
                    self,
                    'Chyba',
                    'Vyberte platný sériový port'
                )
                return

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

    # Menu callbacks

    def open_clone_file(self):
        """Otevře clone soubor"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            'Otevřít clone soubor',
            '',
            'Clone soubory (*.ft897 *.bin);;Všechny soubory (*.*)'
        )

        if filename:
            try:
                with open(filename, 'rb') as f:
                    data = f.read()
                QMessageBox.information(
                    self,
                    'Clone soubor načten',
                    f'Načteno {len(data)} bajtů z {os.path.basename(filename)}'
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Chyba',
                    f'Nelze otevřít soubor:\n{str(e)}'
                )

    def save_clone_file(self):
        """Uloží clone data do souboru"""
        if not hasattr(self, 'clone_data') or not self.clone_data:
            QMessageBox.warning(
                self,
                'Žádná data',
                'Nejprve vyčtěte paměti z radiostanice pomocí menu Klonování.'
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Uložit clone soubor',
            'ft897_clone.bin',
            'Clone soubory (*.ft897 *.bin);;Všechny soubory (*.*)'
        )

        if filename:
            try:
                with open(filename, 'wb') as f:
                    f.write(self.clone_data)
                QMessageBox.information(
                    self,
                    'Uloženo',
                    f'Clone data ({len(self.clone_data)} bajtů) byla uložena do:\n{filename}'
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Chyba',
                    f'Nelze uložit soubor:\n{str(e)}'
                )

    def read_memories(self):
        """Vyčte paměti z radiostanice"""
        if not self.connected:
            QMessageBox.warning(
                self,
                'Nepřipojeno',
                'Nejprve se připojte k radiostanici.'
            )
            return

        # Zobrazit instrukce pro vstup do clone mode
        instructions = QMessageBox(self)
        instructions.setWindowTitle('Příprava Clone Mode')
        instructions.setIcon(QMessageBox.Information)
        instructions.setText('<b>Postup pro vstup do Clone Mode:</b>')
        instructions.setInformativeText(
            '1. <b>VYPNĚTE</b> radiostanici<br>'
            '2. Ujistěte se, že kabel je připojen k <b>CAT/LINEAR</b> konektoru<br>'
            '3. Držte tlačítka <b>[MODE &lt;]</b> a <b>[MODE &gt;]</b><br>'
            '4. Zapněte radiostanici (stále držte tlačítka)<br>'
            '5. Na displeji se objeví <b>"CLONE MODE"</b><br>'
            '6. Uvolněte tlačítka<br>'
            '7. Klikněte <b>OK</b> v tomto okně<br>'
            '8. Během 30 sekund stiskněte <b>[C](SEND)</b> na radiostanici<br><br>'
            '<i>Radiostanice začne odesílat data...</i>'
        )
        instructions.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if instructions.exec_() != QMessageBox.Ok:
            return

        # Dialog s informacemi a progress barem
        dialog = QDialog(self)
        dialog.setWindowTitle('Clone Mode - Čtení pamětí')
        dialog.setModal(True)
        layout = QVBoxLayout()

        info_label = QLabel(
            '<b>Čekám na data z radiostanice...</b><br><br>'
            'Stiskněte tlačítko <b>[C](SEND)</b> na radiostanici!<br><br>'
            'Clone protokol (podle CHIRP):<br>'
            '• Bloková struktura: 13 bloků<br>'
            '• Celková velikost: 7341 bajtů<br>'
            '• Rychlost: 9600 baud<br>'
            '• Ověřování: checksum + ACK'
        )
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        layout.addWidget(progress)

        status_label = QLabel('Zahajuji čtení...')
        layout.addWidget(status_label)

        dialog.setLayout(layout)
        dialog.setMinimumWidth(400)
        dialog.show()

        # Callback pro aktualizaci progressu
        def update_progress(percent):
            progress.setValue(percent)
            status_label.setText(f'Přečteno: {percent}%')
            QApplication.processEvents()

        # Spustit klonování
        self.clone_data = self.radio.clone_memory(progress_callback=update_progress)

        if self.clone_data:
            expected_size = 7341  # Standard FT-897
            success_msg = QMessageBox(self)
            success_msg.setWindowTitle('Clone dokončen')
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setText('<b>Paměti byly úspěšně vyčteny!</b>')

            if len(self.clone_data) == expected_size:
                success_msg.setInformativeText(
                    f'✓ Načteno: <b>{len(self.clone_data)} bajtů</b> (kompletní clone)<br><br>'
                    f'Clone soubor obsahuje:<br>'
                    f'• Všechny paměťové kanály (200 + 10 PMS)<br>'
                    f'• VFO A/B, HOME, QMB konfigurace<br>'
                    f'• Kompletní nastavení radiostanice<br><br>'
                    f'<i>Použijte menu Soubor → Uložit clone soubor pro zálohování.</i>'
                )
            else:
                success_msg.setInformativeText(
                    f'⚠ Načteno: <b>{len(self.clone_data)} bajtů</b><br>'
                    f'(očekáváno {expected_size} bajtů)<br><br>'
                    f'Data mohou být neúplná. Zkuste clone zopakovat.'
                )
            success_msg.exec_()
        else:
            QMessageBox.critical(
                self,
                'Chyba',
                '<b>Chyba při čtení pamětí z radiostanice.</b><br><br>'
                'Možné příčiny:<br>'
                '• Radiostanice není v Clone Mode<br>'
                '• Nestiskli jste [C](SEND) během 30 sekund<br>'
                '• Špatné připojení kabelu<br>'
                '• Rychlost není 9600 baud<br><br>'
                '<i>Zkontrolujte připojení a zkuste to znovu.</i>'
            )

        dialog.close()

        # Znovu připojit na původní baudrate
        if self.radio:
            self.toggle_connection()  # Odpojit
            self.toggle_connection()  # Znovu připojit

    def set_mode(self, mode: str):
        """Nastaví mód z menu"""
        if not self.connected:
            QMessageBox.warning(
                self,
                'Nepřipojeno',
                'Nejprve se připojte k radiostanici.'
            )
            return

        if self.radio.set_mode(mode):
            self.status_bar.showMessage(f'Mód nastaven na {mode}', 3000)
            # Okamžitá aktualizace
            self.update_radio_data()
        else:
            QMessageBox.warning(self, 'Chyba', f'Nelze nastavit mód {mode}')

    def set_frequency_from_menu(self, freq_mhz: float):
        """Nastaví frekvenci z menu pásem"""
        if not self.connected:
            QMessageBox.warning(
                self,
                'Nepřipojeno',
                'Nejprve se připojte k radiostanici.'
            )
            return

        freq_hz = freq_mhz * 1_000_000.0

        if self.radio.set_frequency(freq_hz):
            self.status_bar.showMessage(f'Frekvence nastavena na {freq_mhz} MHz', 3000)
            # Okamžitá aktualizace
            self.update_radio_data()
        else:
            QMessageBox.warning(self, 'Chyba', 'Nelze nastavit frekvenci')

    def show_about(self):
        """Zobrazí dialog O aplikaci"""
        about_text = """
        <h2>FT-897 Radio Reader & Controller</h2>
        <p><b>Verze:</b> 2.0</p>
        <p><b>Popis:</b> Aplikace pro čtení, ovládání a klonování radiostanice Yaesu FT-897</p>

        <h3>Funkce:</h3>
        <ul>
            <li>Zobrazení aktuální frekvence a módu</li>
            <li>Monitoring S-metru, výkonu a dalších parametrů</li>
            <li>Nastavení frekvence a módu</li>
            <li>Rychlý přístup k radioamatérským pásmům (ČR)</li>
            <li>Klonování pamětí z radiostanice (0xBB příkaz)</li>
            <li>Automatická detekce COM portů (Windows/Linux)</li>
        </ul>

        <h3>CAT Protokol:</h3>
        <p>Používá CAT protokol Yaesu pro komunikaci s FT-897</p>
        <p>Podporované rychlosti: 4800, 9600, 38400 baud</p>

        <p><b>73!</b> 📻</p>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('O aplikaci')
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.exec_()


def main():
    """Hlavní funkce aplikace"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Moderní vzhled

    window = FT897ReaderGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
