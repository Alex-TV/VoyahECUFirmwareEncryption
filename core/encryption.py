import os
import base64
import hashlib
from core.crypto_utils import encrypt_file, generate_pkcs7_envelop, sign_file_p7s

def encrypt_files(bin_path, otx_path, save_dir, aes_key, iv, envelop,
                  sign_cert_path, sign_key_path, output_manager, openssl_path="openssl"):
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

def encrypt_otx_files(otx_path, save_dir, aes_key, iv, output_manager):
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