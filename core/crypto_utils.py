import base64
import tempfile
import os
import subprocess
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

def generate_aes_key_iv():
    aes_key = get_random_bytes(32)  # 256-bit
    iv = get_random_bytes(16)
    return aes_key, iv

def encrypt_file(file_path, aes_key, iv):
    with open(file_path, 'rb') as f:
        bin_data = f.read()
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(bin_data, AES.block_size))
    return encrypted

def generate_pkcs7_envelop(aes_key_bytes, cert_path, save_dir, openssl_path="openssl"):
    """Создание PKCS7 конверта с использованием OpenSSL"""
    try:
        # Создаем временные файлы
        with tempfile.NamedTemporaryFile(delete=False, dir=save_dir, suffix='.key') as key_file:
            key_file.write(aes_key_bytes)
            key_file_path = key_file.name
        with tempfile.NamedTemporaryFile(delete=False, dir=save_dir, suffix='.p7m') as p7m_file:
            p7m_file_path = p7m_file.name

        # Используем абсолютные пути для OpenSSL
        abs_key_path = os.path.abspath(key_file_path)
        abs_p7m_path = os.path.abspath(p7m_file_path)
        abs_cert_path = os.path.abspath(cert_path)

        cmd = [
            openssl_path, "cms", "-encrypt",
            "-des3",  # ← 3DES-CBC, а не AES
            "-binary",
            "-in", abs_key_path,
            "-out", abs_p7m_path,
            "-outform", "DER",
            abs_cert_path
        ]
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"OpenSSL stdout: {result.stdout}")
            print(f"OpenSSL stderr: {result.stderr}")
            raise Exception(f"OpenSSL error: {result.stderr}")

        # Читаем результат
        with open(p7m_file_path, 'rb') as f:
            pkcs7_data = f.read()

        # Очищаем временные файлы
        os.unlink(key_file_path)
        os.unlink(p7m_file_path)

        # Кодируем в base64
        s = base64.b64encode(pkcs7_data).decode('utf-8')
        return s
    except Exception as e:
        # В случае ошибки пытаемся очистить временные файлы
        try:
            if 'key_file_path' in locals(): os.unlink(key_file_path)
            if 'p7m_file_path' in locals(): os.unlink(p7m_file_path)
        except:
            pass
        raise e

def sign_file_p7s(input_file, cert_file, key_file, save_dir, openssl_path="openssl"):
    """Подписывает файл в формате PKCS#7 (DER) с помощью OpenSSL"""
    with tempfile.NamedTemporaryFile(delete=False, dir=save_dir, suffix='.p7s') as p7m_file:
        p7m_file_path = p7m_file.name
    try:
        cmd = [
            openssl_path, "cms", "-sign",
            "-in", os.path.abspath(input_file),
            "-out", os.path.abspath(p7m_file_path),
            "-outform", "DER",
            "-signer", os.path.abspath(cert_file),
            "-inkey", os.path.abspath(key_file),
            "-binary",
            "-md", "sha256",
            "-noattr"  # ← Не добавлять атрибуты подписи
        ]
        print(f"Signing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=save_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"OpenSSL sign error: {result.stderr}")
        # Читаем подпись и кодируем в Base64
        with open(p7m_file_path, 'rb') as f:
            der_data = f.read()
        os.unlink(p7m_file_path)
        return base64.b64encode(der_data).decode('utf-8')
    except Exception as e:
        try:
            if 'p7m_file_path' in locals(): os.unlink(p7m_file_path)
        except:
            pass
        raise e