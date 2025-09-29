from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from core.decryption import decrypt_files
from core.settings_manager import SettingsManager

class DecryptionTab(QWidget):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.bin_file_path = None
        self.otx_file_path = None
        self.json_file_path = None
        self.priv_key_path = None
        self.cert_path = None
        self.save_path = None
        self.settings = settings
        self.init_ui()
        self.load_paths_from_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("🔓 Decryption:")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(20)

        # Encrypted Bin file selection
        bin_layout = QHBoxLayout()
        self.bin_path = QLineEdit()
        bin_btn = QPushButton('Select Encrypted Bin File')
        bin_btn.clicked.connect(self.select_bin_file)
        bin_layout.addWidget(QLabel('Encrypted Bin File:'))
        bin_layout.addWidget(self.bin_path)
        bin_layout.addWidget(bin_btn)
        layout.addLayout(bin_layout)

        # Encrypted OTX file selection
        otx_layout = QHBoxLayout()
        self.otx_path = QLineEdit()
        otx_btn = QPushButton('Select Encrypted OTX File')
        otx_btn.clicked.connect(self.select_otx_file)
        otx_layout.addWidget(QLabel('Encrypted OTX File:'))
        otx_layout.addWidget(self.otx_path)
        otx_layout.addWidget(otx_btn)
        layout.addLayout(otx_layout)

        # JSON file selection
        json_layout = QHBoxLayout()
        self.json_path = QLineEdit()
        json_btn = QPushButton('Select JSON File')
        json_btn.clicked.connect(self.select_json_file)
        json_layout.addWidget(QLabel('JSON File:'))
        json_layout.addWidget(self.json_path)
        json_layout.addWidget(json_btn)
        layout.addLayout(json_layout)

        # Private key selection
        priv_key_layout = QHBoxLayout()
        self.priv_key_path_input = QLineEdit()
        priv_key_btn = QPushButton('Select Private Key')
        priv_key_btn.clicked.connect(self.select_priv_key)
        priv_key_layout.addWidget(QLabel('Private Key:'))
        priv_key_layout.addWidget(self.priv_key_path_input)
        priv_key_layout.addWidget(priv_key_btn)
        layout.addLayout(priv_key_layout)

        # Certificate selection
        cert_layout = QHBoxLayout()
        self.cert_path_input = QLineEdit()
        cert_btn = QPushButton('Select Certificate')
        cert_btn.clicked.connect(self.select_cert)
        cert_layout.addWidget(QLabel('Certificate:'))
        cert_layout.addWidget(self.cert_path_input)
        cert_layout.addWidget(cert_btn)
        layout.addLayout(cert_layout)

        # Save directory selection
        save_layout = QHBoxLayout()
        self.save_path_input = QLineEdit()
        save_btn = QPushButton('Select Save Directory')
        save_btn.clicked.connect(self.select_save_dir)
        save_layout.addWidget(QLabel('Save Directory:'))
        save_layout.addWidget(self.save_path_input)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

        # Decrypt button
        decrypt_btn = QPushButton('Decrypt Files')
        decrypt_btn.clicked.connect(self.decrypt_files)
        layout.addWidget(decrypt_btn)

        self.setLayout(layout)

    def select_bin_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Encrypted Bin File', '', 'Encrypted Files (*.enc.full)')
        if file_path:
            self.bin_path.setText(file_path)
            self.bin_file_path = file_path
            self.settings.set_encripted_bin_path(file_path)

    def select_otx_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Encrypted OTX File', '', 'Encrypted Files (*.otx)')
        if file_path:
            self.otx_path.setText(file_path)
            self.otx_file_path = file_path
            self.settings.set_encripted_otx_path(file_path)

    def select_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select JSON Info File', '', 'JSON Files (*.json)')
        if file_path:
            self.json_path.setText(file_path)
            self.json_file_path = file_path

    def select_priv_key(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Private Key', '', 'Key Files (*.key *.pem)')
        if file_path:
            self.priv_key_path_input.setText(file_path)
            self.priv_key_path = file_path

    def select_cert(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Certificate', '', 'Certificate Files (*.crt *.pem)')
        if file_path:
            self.cert_path_input.setText(file_path)
            self.cert_path = file_path

    def select_save_dir(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Save Directory')
        if path:
            self.save_path_input.setText(path)
            self.save_path = path

    def load_paths_from_settings(self):
        """Загружаем пути к файлам из настроек"""
        bin_path = self.settings.get_encripted_bin_path()
        otx_path = self.settings.get_encripted_otx_path()

        if bin_path:
            self.bin_path.setText(bin_path)
            self.bin_file_path = bin_path
        if otx_path:
            self.otx_path.setText(otx_path)
            self.otx_file_path = otx_path

    def decrypt_files(self):
        if not all([self.bin_file_path, self.otx_file_path, self.json_file_path, self.priv_key_path, self.cert_path, self.save_path]):
            QMessageBox.warning(self, 'Error', 'Please select all required files and save directory!')
            return

        openssl_path = self.settings.get_openssl_path()

        try:
            bin_out, otx_out = decrypt_files(
                self.bin_file_path, self.otx_file_path, self.json_file_path,
                self.priv_key_path, self.cert_path, self.save_path, openssl_path
            )

            QMessageBox.information(self, 'Success', f'Files decrypted successfully!\nBin: {bin_out}\nOtx: {otx_out}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Decryption failed: {str(e)}')