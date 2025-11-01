import base64
import tempfile
import os
import hashlib
import subprocess
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pyasn1.codec.der import decoder as der_decoder, encoder as der_encoder
from pyasn1_modules import rfc2315, rfc5652
from pyasn1.type import univ

PKCS1_SHA1_PREFIX = b'\x01' + b'\xff' * 218 + b'\x00\x30\x21\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00\x04\x14'

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

def sign_file_p7s(input_file, cert_file, key_file):
    # 1. Дайджест: SHA-1(SHA-256(data))
    with open(input_file, 'rb') as f:
        data = f.read()
    digest = hashlib.sha1(hashlib.sha256(data).digest()).digest()

    # 2. Raw RSA подпись
    with open(key_file, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("RSA key required")

    digest = PKCS1_SHA1_PREFIX + digest
    n = private_key.private_numbers().public_numbers.n
    d = private_key.private_numbers().d
    m = int.from_bytes(digest, 'big')
    s = pow(m, d, n)
    signature = s.to_bytes(256, 'big')

    # 3. Загрузить сертификат
    with open(cert_file, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    cert_obj, _ = der_decoder.decode(cert_der, asn1Spec=rfc2315.Certificate())

    # 4. Собрать CMS
    content_info = rfc5652.ContentInfo()
    content_info['contentType'] = univ.ObjectIdentifier('1.2.840.113549.1.7.2')

    signed_data = rfc5652.SignedData()
    signed_data['version'] = 1

    da = rfc5652.DigestAlgorithmIdentifier()
    da['algorithm'] = univ.ObjectIdentifier('1.3.14.3.2.26')  # sha1
    da['parameters'] = univ.Null("")
    signed_data['digestAlgorithms'] = rfc5652.DigestAlgorithmIdentifiers()
    signed_data['digestAlgorithms'].setComponentByPosition(0, da)

    eci = rfc5652.EncapsulatedContentInfo()
    eci['eContentType'] = univ.ObjectIdentifier('1.2.840.113549.1.7.1')
    signed_data['encapContentInfo'] = eci

    # === КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: используем existing поле ===
    certs = signed_data['certificates']  # ← уже правильный тип
    cert_choice = rfc5652.CertificateChoices()
    cert_choice.setComponentByPosition(0, cert_obj)
    certs.setComponentByPosition(0, cert_choice)

    # SignerInfo
    signer_info = rfc5652.SignerInfo()
    signer_info['version'] = 1

    issuer_der = cert.issuer.public_bytes(serialization.Encoding.DER)
    issuer_rdns, _ = der_decoder.decode(issuer_der, asn1Spec=rfc2315.Name())
    # Создаём IssuerAndSerialNumber
    issuer_and_sn = rfc5652.IssuerAndSerialNumber()
    issuer_and_sn['issuer'] = issuer_rdns
    issuer_and_sn['serialNumber'] = cert.serial_number

    # Оборачиваем в SignerIdentifier (CHOICE)
    sid = rfc5652.SignerIdentifier()
    sid.setComponentByPosition(0, issuer_and_sn)  # индекс 0 = issuerAndSerialNumber

    # Присваиваем
    signer_info['sid'] = sid

    signer_info['digestAlgorithm'] = da
    sig_algo = rfc5652.SignatureAlgorithmIdentifier()
    sig_algo['algorithm'] = univ.ObjectIdentifier('1.2.840.113549.1.1.1')
    sig_algo['parameters'] = univ.Null("")
    signer_info['signatureAlgorithm'] = sig_algo
    signer_info['signature'] = signature

    signer_infos = signed_data['signerInfos']
    signer_infos.setComponentByPosition(0, signer_info)

    content_info['content'] = signed_data
    cms_der = der_encoder.encode(content_info)
    return base64.b64encode(cms_der).decode('utf-8')

def sign_verify_file_p7s(cms_pem_path: str, data_file_path: str):
    cms_pem = Path(cms_pem_path).read_bytes()
    data = Path(data_file_path).read_bytes()

    # PEM → DER
    cms_der = pem_to_der(cms_pem)

    # Декодируем как ContentInfo (RFC 5652)
    content_info, _ = der_decoder.decode(cms_der, asn1Spec=rfc5652.ContentInfo())

    content_type = content_info['contentType']
    signed_data_oid = univ.ObjectIdentifier('1.2.840.113549.1.7.2')  # id-signedData

    if content_type != signed_data_oid:
        print(f"[!] Не поддерживаемый тип контента: {content_type}")
        return

    # Извлекаем SignedData
    signed_data, _ = der_decoder.decode(
        content_info['content'],
        asn1Spec=rfc5652.SignedData()
    )

    signer_info = signed_data['signerInfos'][0]

    # === Хеш-алгоритм ===
    digest_algo_oid = signer_info['digestAlgorithm']['algorithm']
    hash_cls = get_hash_class(digest_algo_oid)
    if not hash_cls:
        print(f"[!] Неизвестный OID хеша: {digest_algo_oid}")
        return

    print(f"[+] Алгоритм хеширования: {hash_cls.name.upper()}")

    # === Сертификат и ключ ===
    certs = signed_data['certificates']
    if not certs:
        print("[!] Сертификаты не найдены")
        return

    #cert_der = certs[0].asOctets()
    # certs[0] — это CertificateChoices (CHOICE)
    cert_choice = certs[0]
    # Получаем компонент по индексу 0 (certificate)
    cert_der = der_encoder.encode(cert_choice[0])
    cert = x509.load_der_x509_certificate(cert_der)
    pubkey = cert.public_key()

    # === Хеш данных ===
    # === 🔑 СПЕЦИАЛЬНАЯ ЛОГИКА ДЛЯ VOYAH/DFMC ===
    # Подпись применяется к: SHA-1( SHA-256( данные ) )
    print("[+] Используется гибридная схема: SHA-1(SHA-256(данные))")
    inner_hash = hashlib.sha256(data).digest()
    computed_digest = hashlib.sha1(inner_hash).digest()
    print(f"    SHA-256(данные) = {inner_hash.hex()}")
    print(f"    SHA-1(SHA-256)   = {computed_digest.hex()}")

    # === signedAttrs? ===
    # Проверяем, есть ли signedAttrs (поле 4 в SignerInfo)
    if 'signedAttrs' in signer_info and signer_info['signedAttrs'].isValue:
        signed_attrs = signer_info['signedAttrs']
    else:
        signed_attrs = None
    if signed_attrs and len(signed_attrs) > 0:
        print("[+] Подпись с signedAttrs")
        msg_digest = None
        for attr in signed_attrs:
            if attr['attrType'] == univ.ObjectIdentifier('1.2.840.113549.1.9.4'):  # id-messageDigest
                msg_digest = attr['attrValues'][0].asOctets()
                break
        if msg_digest:
            print(f"    messageDigest из подписи: {msg_digest.hex()}")
            print(f"    Хеш файла:                {computed_digest.hex()}")
            if msg_digest == computed_digest:
                print("[OK] messageDigest совпадает")
                content_to_verify = der_encoder.encode(signed_attrs)
            else:
                print("[FAIL] messageDigest НЕ совпадает")
                return
        else:
            print("[!] messageDigest не найден")
            return
    else:
        print("[+] Подпись без signedAttrs")
        content_to_verify = data

    # === Подпись ===
    signature = signer_info['signature'].asOctets()
    print(f"[+] Длина подписи: {len(signature)} байт")

    # === Проверка PKCS#1 ===
    try:
        if isinstance(pubkey, rsa.RSAPublicKey):
            pubkey.verify(signature, content_to_verify, padding.PKCS1v15(), hash_cls())
            print("[OK] Подпись УСПЕШНО проверена (PKCS#1 v1.5)")
        else:
            print("[!] Поддерживается только RSA")
    except Exception as e:
        print(f"[FAIL] PKCS#1 проверка не прошла: {e}")

        # Raw RSA fallback
        if isinstance(pubkey, rsa.RSAPublicKey):
            print("[*] Попытка raw RSA...")
            n = pubkey.public_numbers().n
            e = pubkey.public_numbers().e
            sig_int = int.from_bytes(signature, 'big')
            decrypted_int = pow(sig_int, e, n)
            decrypted = decrypted_int.to_bytes((decrypted_int.bit_length() + 7) // 8, 'big')
            print(f"Полная строка: {decrypted.hex()}")
            if len(decrypted) < 256:
                decrypted = b'\x00' * (256 - len(decrypted)) + decrypted

            # Проверяем, совпадает ли конец с хешем
            if decrypted.endswith(computed_digest):
                print("[OK] Подпись УСПЕШНО проверена (raw RSA, хеш в конце)")
            else:
                print("[FAIL] Raw RSA не прошла")
                print(f"    Последние {len(computed_digest)} байт: {decrypted[-len(computed_digest):].hex()}")
                print(f"    Ожидался хеш: {computed_digest.hex()}")

def get_hash_class(oid):
    oid_to_hash = {
        univ.ObjectIdentifier('1.3.14.3.2.26'): hashes.SHA1,
        univ.ObjectIdentifier('2.16.840.1.101.3.4.2.1'): hashes.SHA256,
        univ.ObjectIdentifier('2.16.840.1.101.3.4.2.2'): hashes.SHA384,
        univ.ObjectIdentifier('2.16.840.1.101.3.4.2.3'): hashes.SHA512,
    }
    return oid_to_hash.get(oid)

def pem_to_der(pem_data: bytes) -> bytes:
    pem_str = pem_data.decode('ascii')
    lines = pem_str.strip().split('\n')
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.startswith('-----BEGIN '):
            start = i
        elif line.startswith('-----END '):
            end = i
            break
    if start is None or end is None:
        raise ValueError("PEM format not recognized")
    base64_data = ''.join(lines[start+1:end])
    return base64.b64decode(base64_data)