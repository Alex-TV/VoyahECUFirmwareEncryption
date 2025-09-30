import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
from core.encryption import encrypt_files, encrypt_otx_files, encrypt_group_file
from core.settings_manager import SettingsManager
from core.output_manager import OutputManager


class EncryptionTab(QWidget):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self.bin_file_path = None
        self.otx_file_path = None
        self.context_pattern_file_path = None
        self.group_path = None
        self.aes_key = None
        self.iv_key = None
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

        single_encrypt_box = QGroupBox("🎯 Single Encryption")
        single_encrypt_layout = QVBoxLayout()
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
        single_encrypt_layout.addLayout(ecu_layout)

        # Bin file selection
        bin_layout = QHBoxLayout()
        self.bin_path = QLineEdit()
        bin_btn = QPushButton('Select Bin File')
        bin_btn.clicked.connect(self.select_bin_file)
        bin_layout.addWidget(QLabel('Bin File:'))
        bin_layout.addWidget(self.bin_path)
        bin_layout.addWidget(bin_btn)
        single_encrypt_layout.addLayout(bin_layout)

        # OTX file selection
        otx_layout = QHBoxLayout()
        self.otx_path = QLineEdit()
        otx_btn = QPushButton('Select OTX File')
        otx_btn.clicked.connect(self.select_otx_file)
        otx_layout.addWidget(QLabel('OTX File:'))
        otx_layout.addWidget(self.otx_path)
        otx_layout.addWidget(otx_btn)
        single_encrypt_layout.addLayout(otx_layout)

        # Buttons
        encrypt_all_btn = QPushButton('Encrypt All Files')
        encrypt_all_btn.clicked.connect(self.encrypt_all)
        single_encrypt_layout.addWidget(encrypt_all_btn)

        encrypt_otx_btn = QPushButton('Encrypt OTX Only')
        encrypt_otx_btn.clicked.connect(self.encrypt_otx_only)
        single_encrypt_layout.addWidget(encrypt_otx_btn)

        single_encrypt_box.setLayout(single_encrypt_layout)
        layout.addWidget(single_encrypt_box)

        group_encrypt_box = QGroupBox("🧩 Group Encryption")
        group_encrypt_layout = QVBoxLayout()

        context_pattern_layout = QHBoxLayout()
        self.context_pattern_file_line = QLineEdit()
        context_pattern_btn = QPushButton('Select Context File')
        context_pattern_btn.clicked.connect(self.select_context_pattern_file)
        context_pattern_layout.addWidget(QLabel('Context File:'))
        context_pattern_layout.addWidget(self.context_pattern_file_line)
        context_pattern_layout.addWidget(context_pattern_btn)
        group_encrypt_layout.addLayout(context_pattern_layout)

        group_layout = QHBoxLayout()
        self.group_path_line = QLineEdit()
        group_btn = QPushButton('Select Group path')
        group_btn.clicked.connect(self.select_group_file)
        group_layout.addWidget(QLabel('Group path:'))
        group_layout.addWidget(self.group_path_line)
        group_layout.addWidget(group_btn)
        group_encrypt_layout.addLayout(group_layout)

        encrypt_froup_btn = QPushButton('Encrypt Group')
        encrypt_froup_btn.clicked.connect(self.encrypt_group)
        group_encrypt_layout.addWidget(encrypt_froup_btn)

        group_encrypt_box.setLayout(group_encrypt_layout)
        layout.addWidget(group_encrypt_box)

        self.setLayout(layout)

    def on_ecu_changed(self, ecu):
        """Переход на новую ECU вызывает пересоздание output_manager."""
        if ecu != self.settings.get_ecu():
            self.settings.set_ecu(ecu)

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
        context_path = self.settings.get_context_pattern_path()
        group_path = self.settings.get_input_group_path()

        if bin_path:
            self.bin_path.setText(bin_path)
            self.bin_file_path = bin_path
        if otx_path:
            self.otx_path.setText(otx_path)
            self.otx_file_path = otx_path
        if ecu:
            self.ecu_combo.setCurrentText(ecu)
        if context_path:
            self.context_pattern_file_line.setText(context_path)
            self.context_pattern_file_path = context_path
        if group_path:
            self.group_path_line.setText(group_path)
            self.group_path = group_path

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

        sign_cert_path = self.settings.get_sign_cert_path()
        sign_key_path = self.settings.get_sign_key_path()
        openssl_path = self.settings.get_openssl_path()
        envelop = self.settings.get_envelop()

        if not cert_path:
            QMessageBox.warning(self, 'Error', 'Please set cert paths in settings!')
            return

        if not envelop:
            QMessageBox.warning(self, 'Error', 'Please generate envelop in settings!')
            return

        output_manager = OutputManager(self.settings)

        try:
            output_json = encrypt_files(
                self.bin_file_path, self.otx_file_path, self.aes_key, self.iv_key,
                envelop, sign_cert_path, sign_key_path, output_manager, openssl_path)
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

        output_manager = OutputManager(self.settings)

        try:
            output_json = encrypt_otx_files(self.otx_file_path, self.aes_key, self.iv_key, output_manager)
            QMessageBox.information(self, 'Success', 'OTX encrypted successfully!')
            print(json.dumps(output_json, indent=2))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Encryption failed: {str(e)}')

    def select_context_pattern_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Context File', '', 'Context Files (*.db)')
        if file_path:
            self.context_pattern_file_line.setText(file_path)
            self.context_pattern_file_path = file_path
            self.settings.set_context_pattern_path(file_path)  # Сохраняем

    def select_group_file(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Group Path')
        if path:
            self.group_path_line.setText(path)
            self.group_path = path
            self.settings.set_input_group_path(path)

    def encrypt_group(self):

        if not all([self.context_pattern_file_path, self.group_path]):
            QMessageBox.warning(self, 'Error', 'Please select context and input path!')
            return

        if not self.aes_key:
            QMessageBox.warning(self, 'Error', 'Please generate AES keys first!')
            return

        try:
            encrypt_group_file(self.context_pattern_file_path, self.group_path,
                               self.aes_key, self.iv_key, self.settings)
            QMessageBox.information(self, 'Success', 'All Ecus encrypted successfully!')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Encryption failed: {str(e)}')
