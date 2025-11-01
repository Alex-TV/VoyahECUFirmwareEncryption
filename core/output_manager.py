import json
import os
from core.settings_manager import SettingsManager

class OutputManager:
    # ✅ Структура JSON по умолчанию
    DEFAULT_JSON = {
        "ecu": "",
        "file_sha": "",
        "algorithm": "AES",
        "envelop": "",
        "iv": "",
        "length": 256,
        "transformation": "AES/CBC/PKCS7Padding",
        "original_file_sign": "",
        "upgrade_spec_sha": "",
        "upgrade_spec_algorithm": "AES",
        "upgrade_spec_envelop": "",
        "upgrade_spec_iv": "",
        "upgrade_spec_length": 256,
        "upgrade_spec_transformation": "AES/CBC/PKCS7Padding",
        "upgrade_spec_sign": "",
    }

    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.ecu = self.settings.get_ecu()
        self.save_dir = self.settings.get_output_path()
        self.ecu_dir = None
        self.json_path = None
        self.data = {}
        self._init_ecu_directory()

    def _init_ecu_directory(self):
        """Создаёт папку ECU в save_dir, если не существует, и инициализирует JSON."""
        if not self.ecu or not self.save_dir:
            raise ValueError("ECU or Save Directory not set in settings.")

        self.ecu_dir = os.path.join(self.save_dir, self.ecu)
        os.makedirs(self.ecu_dir, exist_ok=True)

        self.json_path = os.path.join(self.ecu_dir, 'firmware_info.json')

        if not os.path.exists(self.json_path):
            self.data = self.DEFAULT_JSON.copy()
            self.data["ecu"] = self.ecu
            self.save_json()
        else:
            self.load_json()

    def load_json(self):
        """Загружает JSON из файла."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save_json(self):
        """Сохраняет JSON в файл."""
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def update_json(self, new_data):
        """Обновляет JSON новыми данными и сохраняет."""
        self.data.update(new_data)
        self.save_json()

    def set_ecu(self, ecu):
        """Переключает ECU, пересоздаёт директорию и JSON."""
        self.settings.set_ecu(ecu)
        self.ecu = ecu
        self._init_ecu_directory()

    def get_ecu_dir(self):
        return self.ecu_dir

    def get_json_path(self):
        return self.json_path

    def get_data(self):
        return self.data