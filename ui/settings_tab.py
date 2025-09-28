import binascii
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from core.crypto_utils import generate_aes_key_iv
from core.settings_manager import SettingsManager
from core.encryption import generate_pkcs7_envelop

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.aes_key = None
        self.iv_key = None
        self.envelop = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # OpenSSL path
        openssl_layout = QHBoxLayout()
        openssl_layout.addWidget(QLabel('OpenSSL Path:'))
        self.openssl_path = QLineEdit()
        openssl_btn = QPushButton('Browse')
        openssl_btn.clicked.connect(self.select_openssl)
        openssl_layout.addWidget(self.openssl_path)
        openssl_layout.addWidget(openssl_btn)
        layout.addLayout(openssl_layout)

        # Certificate for encryption
        cert_layout = QHBoxLayout()
        cert_layout.addWidget(QLabel('Encryption Cert:'))
        self.cert_path = QLineEdit()
        cert_btn = QPushButton('Browse')
        cert_btn.clicked.connect(self.select_cert)
        cert_layout.addWidget(self.cert_path)
        cert_layout.addWidget(cert_btn)
        layout.addLayout(cert_layout)

        # Sign cert and key
        sign_cert_layout = QHBoxLayout()
        sign_cert_layout.addWidget(QLabel('Sign Cert:'))
        self.sign_cert_path = QLineEdit()
        sign_cert_btn = QPushButton('Browse')
        sign_cert_btn.clicked.connect(self.select_sign_cert)
        sign_cert_layout.addWidget(self.sign_cert_path)
        sign_cert_layout.addWidget(sign_cert_btn)
        layout.addLayout(sign_cert_layout)

        sign_key_layout = QHBoxLayout()
        sign_key_layout.addWidget(QLabel('Sign Key:'))
        self.sign_key_path = QLineEdit()
        sign_key_btn = QPushButton('Browse')
        sign_key_btn.clicked.connect(self.select_sign_key)
        sign_key_layout.addWidget(self.sign_key_path)
        sign_key_layout.addWidget(sign_key_btn)
        layout.addLayout(sign_key_layout)

        # Save directory
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel('Save Directory:'))
        self.save_path = QLineEdit()
        save_btn = QPushButton('Browse')
        save_btn.clicked.connect(self.select_save_dir)
        save_layout.addWidget(self.save_path)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)

        # Generate AES Keys
        gen_aes_btn = QPushButton('Generate AES Key & IV')
        gen_aes_btn.clicked.connect(self.generate_aes)
        layout.addWidget(gen_aes_btn)

        # Display generated keys
        self.aes_key_label = QLabel('❌ AES Key: Not Generated')
        self.iv_key_label = QLabel('❌ IV Key: Not Generated')
        self.envelop_label = QLabel('❌ Envelop: Not Generated')
        layout.addWidget(self.aes_key_label)
        layout.addWidget(self.iv_key_label)
        layout.addWidget(self.envelop_label)

        self.setLayout(layout)

    def select_openssl(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select OpenSSL Executable', '', 'Executable Files (*.exe);;All Files (*)')
        if path:
            self.openssl_path.setText(path)
            self.settings.set_openssl_path(path)

    def select_cert(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Certificate', '', 'Certificate Files (*.crt *.pem)')
        if path:
            self.cert_path.setText(path)
            self.settings.set_cert_path(path)
        if self.aes_key and self.iv_key:
            self.envelop = generate_pkcs7_envelop(self.aes_key, path, self.save_path.text(), self.openssl_path.text())
            self.envelop_label.setText(f'Envelop: ✅ Generated')
            self.settings.set_envelop(self.envelop)

    def select_sign_cert(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Sign Certificate', '', 'Certificate Files (*.crt *.pem)')
        if path:
            self.sign_cert_path.setText(path)
            self.settings.set_sign_cert_path(path)

    def select_sign_key(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Sign Key', '', 'Key Files (*.key *.pem)')
        if path:
            self.sign_key_path.setText(path)
            self.settings.set_sign_key_path(path)

    def select_save_dir(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Save Directory')
        if path:
            self.save_path.setText(path)
            self.settings.set_save_path(path)

    def generate_aes(self):
        self.aes_key, self.iv_key = generate_aes_key_iv()
        self.envelop = generate_pkcs7_envelop(self.aes_key, self.cert_path.text(), self.save_path.text(), self.openssl_path.text())
        self.settings.set_aes_key(self.aes_key)
        self.settings.set_iv_key(self.iv_key)
        self.settings.set_envelop(self.envelop)
        self.aes_key_label.setText(f'✅ AES Key: {binascii.hexlify(self.aes_key).decode()}')
        self.iv_key_label.setText(f'✅ IV Key: {binascii.hexlify(self.iv_key).decode()}')
        self.envelop_label.setText(f'✅ Envelop: Generated')

    def load_settings(self):
        self.openssl_path.setText(self.settings.get_openssl_path())
        self.cert_path.setText(self.settings.get_cert_path())
        self.sign_cert_path.setText(self.settings.get_sign_cert_path())
        self.sign_key_path.setText(self.settings.get_sign_key_path())
        self.save_path.setText(self.settings.get_save_path())

        self.aes_key = self.settings.get_aes_key()
        self.iv_key = self.settings.get_iv_key()
        self.envelop = self.settings.get_envelop()

        if self.aes_key and self.iv_key and self.envelop:
            self.aes_key_label.setText(f'✅ AES Key: {binascii.hexlify(self.aes_key).decode()}')
            self.iv_key_label.setText(f'✅ IV Key: {binascii.hexlify(self.iv_key).decode()}')
            self.envelop_label.setText(f'✅ Envelop: Generated')