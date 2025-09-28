import os
import tempfile
import subprocess
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import binascii

def decrypt_file(encrypted_file_path, aes_key, iv):
    """
    Расшифровывает файл с использованием AES (CBC, PKCS7Padding)
    """
    with open(encrypted_file_path, 'rb') as f:
        encrypted_data = f.read()
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return decrypted

def decrypt_pkcs7_envelop(p7m_data_b64, key_file_path, cert_file_path, save_dir, openssl_path="openssl"):
    """
    Расшифровывает PKCS#7 envelop (AES ключ), используя OpenSSL
    """
    try:
        p7m_data = binascii.a2b_base64(p7m_data_b64)

        with tempfile.NamedTemporaryFile(delete=False, dir=save_dir, suffix='.p7m') as p7m_file:
            p7m_file.write(p7m_data)
            p7m_path = p7m_file.name

        with tempfile.NamedTemporaryFile(delete=False, dir=save_dir, suffix='.key') as key_file:
            key_file_path_out = key_file.name

        abs_p7m_path = os.path.abspath(p7m_path)
        abs_key_out_path = os.path.abspath(key_file_path_out)
        abs_cert_path = os.path.abspath(cert_file_path)
        abs_key_path = os.path.abspath(key_file_path)

        cmd = [
            openssl_path, "cms", "-decrypt",
            "-in", abs_p7m_path,
            "-out", abs_key_out_path,
            "-recip", abs_cert_path,
            "-inkey", abs_key_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"OpenSSL decrypt envelop stdout: {result.stdout}")
            print(f"OpenSSL decrypt envelop stderr: {result.stderr}")
            raise Exception(f"OpenSSL decrypt envelop error: {result.stderr}")

        with open(key_file_path_out, 'rb') as f:
            aes_key = f.read()

        # Очищаем временные файлы
        os.unlink(p7m_path)
        os.unlink(key_file_path_out)

        return aes_key
    except Exception as e:
        try:
            if 'p7m_path' in locals(): os.unlink(p7m_path)
            if 'key_file_path_out' in locals(): os.unlink(key_file_path_out)
        except:
            pass
        raise e

def decrypt_files(bin_enc_path, otx_enc_path, json_path, private_key_path, cert_path, save_dir, openssl_path="openssl"):
    """
    Выполняет полную расшифровку bin и otx файлов на основе JSON и ключей.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Получаем IV из JSON
    iv_b64 = data.get("iv") or data.get("upgrade_spec_iv")
    if not iv_b64:
        raise ValueError("IV not found in JSON.")
    iv = binascii.a2b_base64(iv_b64)

    # Расшифровываем AES ключ из envelop
    envelop_b64 = data.get("envelop") or data.get("upgrade_spec_envelop")
    if not envelop_b64:
        raise ValueError("Envelop (encrypted AES key) not found in JSON.")
    aes_key = decrypt_pkcs7_envelop(envelop_b64, private_key_path, cert_path, save_dir, openssl_path)

    # Расшифровываем файлы
    decrypted_bin = decrypt_file(bin_enc_path, aes_key, iv)
    decrypted_otx = decrypt_file(otx_enc_path, aes_key, iv)

    # Сохраняем расшифрованные файлы
    bin_output_path = os.path.join(save_dir, "decrypted.bin")
    otx_output_path = os.path.join(save_dir, "decrypted.otx.gz")  # или .otx, если не gzip

    with open(bin_output_path, 'wb') as f:
        f.write(decrypted_bin)
    with open(otx_output_path, 'wb') as f:
        f.write(decrypted_otx)

    return bin_output_path, otx_output_path