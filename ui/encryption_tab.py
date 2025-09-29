import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from core.encryption import encrypt_files, encrypt_otx_files
from core.settings_manager import SettingsManager
from core.output_manager import OutputManager

class EncryptionTab(QWidget):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.bin_file_path = None
        self.otx_file_path = None
        self.aes_key = None
        self.iv_key = None
        self.settings = settings
        self.load_aes_keys()
        self.init_ui()
        self.load_paths_from_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("🔐 Encryption:")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(20)

        # ECU selection
        ecu_layout = QHBoxLayout()
        ecu_layout.addWidget(QLabel('ECU:'))
        self.ecu_combo = QComboBox()
        self.ecu_combo.addItems(
            ['AC', 'ADCU', 'AMP', 'ASC', 'BCM', 'BLE', 'BMS', 'DSCU', 'EMS', 'EPB', 'EPS', 'ESP',
             'GCU', 'GTW', 'HCML', 'HCMR', 'IVI_MCU', 'IVI_MPU', 'MCUF0', 'MCUR0', 'MPC', 'MRR',
             'MRR_FL', 'MRR_FR', 'MRR_RL', 'MRR_RR', 'OBC', 'POT', 'SWM', 'T-BOX', 'VCU', 'WCM'])
        self.ecu_combo.currentTextChanged.connect(self.on_ecu_changed)
        ecu_layout.addWidget(self.ecu_combo)
        layout.addLayout(ecu_layout)

        # Bin file selection
        bin_layout = QHBoxLayout()
        self.bin_path = QLineEdit()
        bin_btn = QPushButton('Select Bin File')
        bin_btn.clicked.connect(self.select_bin_file)
        bin_layout.addWidget(QLabel('Bin File:'))
        bin_layout.addWidget(self.bin_path)
        bin_layout.addWidget(bin_btn)
        layout.addLayout(bin_layout)

        # OTX file selection
        otx_layout = QHBoxLayout()
        self.otx_path = QLineEdit()
        otx_btn = QPushButton('Select OTX File')
        otx_btn.clicked.connect(self.select_otx_file)
        otx_layout.addWidget(QLabel('OTX File:'))
        otx_layout.addWidget(self.otx_path)
        otx_layout.addWidget(otx_btn)
        layout.addLayout(otx_layout)


        # Buttons
        encrypt_all_btn = QPushButton('Encrypt All Files')
        encrypt_all_btn.clicked.connect(self.encrypt_all)
        layout.addWidget(encrypt_all_btn)

        encrypt_otx_btn = QPushButton('Encrypt OTX Only')
        encrypt_otx_btn.clicked.connect(self.encrypt_otx_only)
        layout.addWidget(encrypt_otx_btn)

        self.setLayout(layout)

    def on_ecu_changed(self, ecu):
        """Переход на новую ECU вызывает пересоздание output_manager."""
        if ecu != self.settings.get_ecu():
            self.settings.set_ecu(ecu)
            self.output_manager = OutputManager(self.settings)

    def select_bin_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Bin File', '', 'Bin Files (*.bin)')
        if file_path:
            self.bin_path.setText(file_path)
            self.bin_file_path = file_path
            self.settings.set_bin_path(file_path)  # Сохраняем

    def select_otx_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select OTX File', '', 'OTX Files (*.gz)')
        if file_path:
            self.otx_path.setText(file_path)
            self.otx_file_path = file_path
            self.settings.set_otx_path(file_path)  # Сохраняем

    def load_paths_from_settings(self):
        """Загружаем пути к файлам из настроек"""
        bin_path = self.settings.get_bin_path()
        otx_path = self.settings.get_otx_path()
        ecu = self.settings.get_ecu()

        if bin_path:
            self.bin_path.setText(bin_path)
            self.bin_file_path = bin_path
        if otx_path:
            self.otx_path.setText(otx_path)
            self.otx_file_path = otx_path
        if ecu:
            self.ecu_combo.setCurrentText(ecu)
            self.output_manager = OutputManager(self.settings)

    def load_aes_keys(self):
        """Загружаем AES ключи из настроек"""
        self.aes_key = self.settings.get_aes_key()
        self.iv_key = self.settings.get_iv_key()

    def encrypt_all(self):
        ecu = self.ecu_combo.currentText()
        self.settings.set_ecu(ecu)  # Сохраняем ECU

        if not all([self.bin_file_path, self.otx_file_path]):
            QMessageBox.warning(self, 'Error', 'Please select bin and otx files!')
            return
        if not self.aes_key:
            QMessageBox.warning(self, 'Error', 'Please generate AES keys first!')
            return

        cert_path = self.settings.get_cert_path()
        save_path = self.output_manager.get_ecu_dir()
        sign_cert_path = self.settings.get_sign_cert_path()
        sign_key_path = self.settings.get_sign_key_path()
        openssl_path = self.settings.get_openssl_path()
        envelop = self.settings.get_envelop()

        if not all([cert_path, save_path]):
            QMessageBox.warning(self, 'Error', 'Please set cert and save paths in settings!')
            return

        try:
            output_json = encrypt_files(
                self.bin_file_path, self.otx_file_path, save_path, self.aes_key, self.iv_key,
                envelop, sign_cert_path, sign_key_path, self.output_manager, openssl_path)
            QMessageBox.information(self, 'Success', 'Files encrypted successfully!')
            print(json.dumps(output_json, indent=2))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Encryption failed: {str(e)}')

    def encrypt_otx_only(self):
        if not self.otx_file_path:
            QMessageBox.warning(self, 'Error', 'Please select otx file!')
            return
        if not self.aes_key:
            QMessageBox.warning(self, 'Error', 'Please generate AES keys first!')
            return

        save_path = self.output_manager.get_ecu_dir()

        if not save_path:
            QMessageBox.warning(self, 'Error', 'Please set save path in settings!')
            return

        try:
            output_json = encrypt_otx_files(self.otx_file_path, save_path, self.aes_key, self.iv_key, self.output_manager)
            QMessageBox.information(self, 'Success', 'OTX encrypted successfully!')
            print(json.dumps(output_json, indent=2))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Encryption failed: {str(e)}')