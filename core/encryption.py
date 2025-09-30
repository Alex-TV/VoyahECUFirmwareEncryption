import os
import base64
import hashlib
import json
import sqlite3

from core.crypto_utils import encrypt_file, generate_pkcs7_envelop, sign_file_p7s
from core.output_manager import OutputManager


def encrypt_files(bin_path, otx_path, aes_key, iv, envelop,
                  sign_cert_path, sign_key_path, output_manager, openssl_path="openssl"):
    save_dir = output_manager.get_ecu_dir()
    if not save_dir:
        raise ValueError("Please set save path in settings!")

    encrypted_bin = encrypt_file(bin_path, aes_key, iv)
    encrypted_otx = encrypt_file(otx_path, aes_key, iv)

    # Calculate file hashes
    bin_sha = hashlib.sha256(encrypted_bin).hexdigest()
    otx_sha = hashlib.sha256(encrypted_otx).hexdigest()

    # Create file names with hashes
    bin_filename = f"{bin_sha}.enc.full"
    otx_filename = f"{otx_sha}.otx"

    # Save encrypted files
    encrypted_bin_path = os.path.join(save_dir, bin_filename)
    encrypted_otx_path = os.path.join(save_dir, otx_filename)

    with open(encrypted_bin_path, 'wb') as f:
        f.write(encrypted_bin)
    with open(encrypted_otx_path, 'wb') as f:
        f.write(encrypted_otx)

    # Подпись оригинальных (НЕ зашифрованных) файлов
    bin_signature = None
    otx_signature = None
    if sign_cert_path and sign_key_path and os.path.exists(sign_cert_path) and os.path.exists(sign_key_path):
        bin_signature = sign_file_p7s(bin_path, sign_cert_path, sign_key_path, save_dir, openssl_path)
        otx_signature = sign_file_p7s(otx_path, sign_cert_path, sign_key_path, save_dir, openssl_path)

    # Generate output JSON

    data = output_manager.get_data()
    data["file_sha"] = bin_sha
    data["envelop"] = envelop
    data["iv"] = base64.b64encode(iv).decode()
    data["original_file_sign"] = bin_signature
    data["upgrade_spec_sha"] = otx_sha
    data["upgrade_spec_envelop"] = envelop
    data["upgrade_spec_iv"] = base64.b64encode(iv).decode()
    data["upgrade_spec_sign"] = otx_signature
    # Save JSON
    output_manager.update_json(data)

    return data


def encrypt_otx_files(otx_path, aes_key, iv, output_manager):
    save_dir = output_manager.get_ecu_dir()
    if not save_dir:
        raise ValueError("Please set save path in settings!")

    encrypted_otx = encrypt_file(otx_path, aes_key, iv)
    otx_sha = hashlib.sha256(encrypted_otx).hexdigest()
    otx_filename = f"{otx_sha}.otx"

    encrypted_otx_path = os.path.join(save_dir, otx_filename)
    with open(encrypted_otx_path, 'wb') as f:
        f.write(encrypted_otx)

    # Чтение JSON
    data = output_manager.get_data()

    # Обновление JSON
    data["upgrade_spec_sha"] = otx_sha
    data["upgrade_spec_envelop"] = data["envelop"]
    data["upgrade_spec_iv"] = base64.b64encode(iv).decode()

    # Сохранение
    output_manager.update_json(data)

    return data


def encrypt_group_file(context_path, group_path, aes_key, iv, settings):
    cert_path = settings.get_cert_path()
    sign_cert_path = settings.get_sign_cert_path()
    sign_key_path = settings.get_sign_key_path()
    openssl_path = settings.get_openssl_path()
    envelop = settings.get_envelop()

    if not cert_path:
        raise ValueError('Please set cert paths in settings!')

    if not envelop:
        raise ValueError('Please generate envelop in settings!')

    # Подключаемся к базе данных
    conn = sqlite3.connect(context_path)
    cursor = conn.cursor()

    # Читаем текущую запись из ota_task
    cursor.execute("SELECT taskData FROM ota_task WHERE type = 'task_info'")
    row = cursor.fetchone()
    ecu_default = settings.get_ecu()

    if not row:
        raise ValueError("Запись с type='task_info' не найдена в таблице ota_task")

    task_data = json.loads(row[0])
    packages_info = task_data.get('packages_info', [])

    for package in packages_info:
        ecu_name = package.get('ecu')
        ecu_version = package.get('display_version')
        ecu_version_code = package.get('version_code')
        bin_pas = os.path.join(group_path, ecu_name, f"0.0.{ecu_version_code}-{ecu_version}", "firmware.bin")
        otx_pas = os.path.join(group_path, ecu_name, f"0.0.{ecu_version_code}-{ecu_version}", "otx.tar.gz")

        if not os.path.exists(bin_pas) or not os.path.exists(otx_pas):
            conn.close()
            settings.set_ecu(ecu_default)
            raise ValueError('f"Файлы для {ecu_name} не найдены, пропускаем.')

        # TODO: создать для setting транзакцию, что бы не сохраняло каждый раз, сейчас это костыль
        settings.set_ecu(ecu_name)
        output_manager = OutputManager(settings)

        encrypt_files(bin_pas, otx_pas, aes_key, iv, envelop, sign_cert_path,
                      sign_key_path, output_manager, openssl_path)
    conn.close()
    settings.set_ecu(ecu_default)
