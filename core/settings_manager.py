import configparser
import os
import binascii

class SettingsManager:
    def __init__(self, settings_file='setting.ini'):
        self.settings_file = settings_file
        self.config = configparser.ConfigParser()
        self._load()

    def _load(self):
        if os.path.exists(self.settings_file):
            self.config.read(self.settings_file)

    def save(self):
        with open(self.settings_file, 'w') as f:
            self.config.write(f)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self.config.has_section(section) and section != 'DEFAULT':
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save()

    # Convenience methods for common settings
    def get_openssl_path(self):
        return self.get('DEFAULT', 'openssl_path', fallback='openssl')

    def set_openssl_path(self, path):
        self.set('DEFAULT', 'openssl_path', path)

    def get_cert_path(self):
        return self.get('DEFAULT', 'cert_path', fallback='')

    def set_cert_path(self, path):
        self.set('DEFAULT', 'cert_path', path)

    def get_sign_cert_path(self):
        return self.get('DEFAULT', 'sign_cert_path', fallback='')

    def set_sign_cert_path(self, path):
        self.set('DEFAULT', 'sign_cert_path', path)

    def get_sign_key_path(self):
        return self.get('DEFAULT', 'sign_key_path', fallback='')

    def set_sign_key_path(self, path):
        self.set('DEFAULT', 'sign_key_path', path)

    def get_output_path(self):
        return self.get('DEFAULT', 'output_path', fallback='')

    def set_output_path(self, path):
        self.set('DEFAULT', 'output_path', path)

    def get_bin_path(self):
        return self.get('ENCRYPTION', 'bin_path', fallback='')

    def set_bin_path(self, path):
        self.set('ENCRYPTION', 'bin_path', path)

    def get_encripted_bin_path(self):
        return self.get('DEFAULT', 'encripted_bin_path', fallback='')

    def set_encripted_bin_path(self, path):
        self.set('DEFAULT', 'encripted_bin_path', path)

    def get_otx_path(self):
        return self.get('ENCRYPTION', 'otx_path', fallback='')

    def set_otx_path(self, path):
        self.set('ENCRYPTION', 'otx_path', path)

    def set_encripted_otx_path(self, path):
        self.set('DEFAULT', 'encripted_otx_path', path)

    def get_encripted_otx_path(self):
        return self.get('DEFAULT', 'encripted_otx_path', fallback='')

    def get_ecu(self):
        return self.get('ENCRYPTION', 'ecu', fallback='')

    def set_ecu(self, ecu):
        self.set('ENCRYPTION', 'ecu', ecu)

    # AES Keys
    def get_aes_key(self):
        hex_key = self.get('AES_KEYS', 'aes_key', fallback=None)
        if hex_key:
            return binascii.unhexlify(hex_key)
        return None

    def set_aes_key(self, key_bytes):
        hex_key = binascii.hexlify(key_bytes).decode()
        self.set('AES_KEYS', 'aes_key', hex_key)

    def get_iv_key(self):
        hex_iv = self.get('AES_KEYS', 'iv_key', fallback=None)
        if hex_iv:
            return binascii.unhexlify(hex_iv)
        return None

    def set_iv_key(self, iv_bytes):
        hex_iv = binascii.hexlify(iv_bytes).decode()
        self.set('AES_KEYS', 'iv_key', hex_iv)

    def set_envelop(self, envelop):
        self.set('AES_KEYS', 'envelop', envelop)

    def get_envelop(self):
        return self.get('AES_KEYS', 'envelop', fallback=None)

    def get_context_path(self):
        return self.get('CONTEXT', 'context_path', fallback=None)

    def set_context_path(self, file_path):
        self.set('CONTEXT', 'context_path', file_path)
