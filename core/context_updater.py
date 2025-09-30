import json
import os
import sqlite3

def update_context_db(db_path, base_dir):
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Читаем текущую запись из ota_task
    cursor.execute("SELECT taskData FROM ota_task WHERE type = 'task_info'")
    row = cursor.fetchone()
    if not row:
        raise ValueError("Запись с type='task_info' не найдена в таблице ota_task")

    task_data = json.loads(row[0])
    packages_info = task_data.get('packages_info', [])

    # Создаём словарь для быстрого доступа к пакетам по ecu
    packages_map = {pkg['ecu']: pkg for pkg in packages_info if 'ecu' in pkg}

    # Проходим по всем папкам в base_dir
    for ecu_name in os.listdir(base_dir):
        ecu_path = os.path.join(base_dir, ecu_name)
        if not os.path.isdir(ecu_path):
            continue

        firmware_info_path = os.path.join(ecu_path, 'firmware_info.json')
        if not os.path.exists(firmware_info_path):
            continue

        # Проверяем, есть ли такой ecu в packages_info
        if ecu_name not in packages_map:
            print(f"Блок {ecu_name} не найден в packages_info, пропускаем.")
            continue

        with open(firmware_info_path, 'r', encoding='utf-8') as f:
            firmware_info = json.load(f)

        target_package = packages_map[ecu_name]

        # Получаем текущий encrypt_info
        encrypt_info_str = target_package.get('encrypt_info', '{}')
        encrypt_info = json.loads(encrypt_info_str)

        bin_sha_file = None
        otx_sha_file = None

        if 'file_sha' in firmware_info and firmware_info['file_sha'] is not None:
            bin_sha_file = firmware_info["file_sha"]
        if 'upgrade_spec_sha' in firmware_info and firmware_info['upgrade_spec_sha'] is not None:
            otx_sha_file = firmware_info["upgrade_spec_sha"]

        # Обновляем нужные поля
        if 'envelop' in firmware_info and firmware_info['envelop'] is not None:
            encrypt_info.setdefault('file_encrypt_info', {})['envelop'] = firmware_info['envelop']
        if 'iv' in firmware_info and firmware_info['iv'] is not None:
            encrypt_info.setdefault('file_encrypt_info', {})['iv'] = firmware_info['iv']
        if 'algorithm' in firmware_info and firmware_info['algorithm'] is not None:
            encrypt_info.setdefault('file_encrypt_info', {})['algorithm'] = firmware_info['algorithm']
        if 'transformation' in firmware_info and firmware_info['transformation'] is not None:
            encrypt_info.setdefault('file_encrypt_info', {})['transformation'] = firmware_info['transformation']
        if 'length' in firmware_info and firmware_info['length'] is not None:
            encrypt_info.setdefault('file_encrypt_info', {})['length'] = firmware_info['length']

        if 'upgrade_spec_envelop' in firmware_info and firmware_info['upgrade_spec_envelop'] is not None:
            encrypt_info.setdefault('upgrade_spec_encrypt_info', {})['envelop'] = firmware_info['upgrade_spec_envelop']
        if 'upgrade_spec_iv' in firmware_info and firmware_info['upgrade_spec_iv'] is not None:
            encrypt_info.setdefault('upgrade_spec_encrypt_info', {})['iv'] = firmware_info['upgrade_spec_iv']
        if 'upgrade_spec_algorithm' in firmware_info and firmware_info['upgrade_spec_algorithm'] is not None:
            encrypt_info.setdefault('upgrade_spec_encrypt_info', {})['algorithm'] = firmware_info['upgrade_spec_algorithm']
        if 'upgrade_spec_transformation' in firmware_info and firmware_info['upgrade_spec_transformation'] is not None:
            encrypt_info.setdefault('upgrade_spec_encrypt_info', {})['transformation'] = firmware_info['upgrade_spec_transformation']
        if 'upgrade_spec_length' in firmware_info and firmware_info['upgrade_spec_length'] is not None:
            encrypt_info.setdefault('upgrade_spec_encrypt_info', {})['length'] = firmware_info['upgrade_spec_length']

        # Обратно в строку и сохраняем в пакете
        target_package['encrypt_info'] = json.dumps(encrypt_info, ensure_ascii=False)

        target_package['end_flash_time'] = 0
        target_package["start_flash_time"] = 0
        target_package["flash_finish"] = 'false'
        target_package["end_rollback_time"] = 0
        target_package["start_rollback_time"] = 0

        if bin_sha_file is not None and otx_sha_file is not None:

            target_package["file_sha"] = bin_sha_file
            target_package["upgrade_spec_sha"] = otx_sha_file

            if ecu_name == 'IVI_MCU' or ecu_name == 'IVI_MPU':
                target_package["file"] = f"/mnt/ota/data/fota/download/{ecu_name}/{bin_sha_file}.enc.full"
                target_package["upgrade_spec_file"] = f"/mnt/ota/data/fota/download/{ecu_name}/{otx_sha_file}.otx"
            else:
                target_package["file"] = f"/mnt/ota/data/fota/download/{ecu_name}/{bin_sha_file}.enc.full"
                target_package["upgrade_spec_file"] = f"/mnt/ota/data/fota/download/{ecu_name}/{otx_sha_file}.otx"

        # if 'original_file_sign' in firmware_info and firmware_info['original_file_sign'] is not None:
        #     target_package['original_file_sign'] = firmware_info['original_file_sign']
        # if 'upgrade_spec_sign' in firmware_info and firmware_info['upgrade_spec_sign'] is not None:
        #     target_package['upgrade_spec_sign'] = firmware_info['upgrade_spec_sign']

    # Обновляем JSON в базе
    updated_task_data = json.dumps(task_data, ensure_ascii=False)
    cursor.execute("UPDATE ota_task SET taskData = ? WHERE type = ?", (updated_task_data, 'task_info'))

    # Сохраняем и закрываем
    conn.commit()
    conn.close()

def clear_context_db(db_path, target_version, remove_ivi):
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Читаем текущую запись из ota_task
    cursor.execute("SELECT taskData FROM ota_task WHERE type = 'task_info'")
    row = cursor.fetchone()
    if not row:
        raise ValueError("Запись с type='task_info' не найдена в таблице ota_task")

    task_data = json.loads(row[0])

    if remove_ivi:
        ecu_names_to_remove = {'IVI_MCU', 'IVI_MPU'}
        task_data['packages_info'] = [pkg for pkg in task_data['packages_info']
                                      if pkg.get('ecu') not in ecu_names_to_remove]

    packages_info = task_data.get('packages_info', [])

    if 'download_state' in task_data:
        if 'fail_info' in task_data['download_state']:
            del task_data['download_state']['fail_info']
        if 'fail_reason'in task_data['download_state']:
            del task_data['download_state']['fail_reason']
        if 'stage' in task_data['download_state']:
            task_data['download_state']['stage'] = "Retrive Packages"

    if 'flash_state' in task_data:
        del task_data['flash_state']
    if 'overall_state' in task_data:
        if 'stage' in task_data['overall_state']:
            task_data['overall_state']['stage'] = "Download"
        if 'state' in task_data['overall_state']:
            task_data['overall_state']['state'] = "Process"

    # Проходим по всем пакетам и очищаем encrypt_info
    for target_package in packages_info:
        if 'end_flash_time' in target_package:
            target_package['end_flash_time'] = 0
        if 'start_flash_time' in target_package:
            target_package["start_flash_time"] = 0
        if 'flash_finish' in target_package:
            target_package["flash_finish"] = 'false'
        if 'end_rollback_time' in target_package:
            target_package["end_rollback_time"] = 0
        if 'start_rollback_time' in target_package:
            target_package["start_rollback_time"] = 0
        if 'base_sw_version' in target_package:
            target_package["base_sw_version"] = 0

    if 'schedule_state' in task_data:
        del task_data['schedule_state']
    if 'target_baseline_version' in task_data:
        task_data['target_baseline_version'] = target_version

    # Обновляем JSON в базе
    updated_task_data = json.dumps(task_data, ensure_ascii=False)
    cursor.execute("UPDATE ota_task SET taskData = ? WHERE type = ?", (updated_task_data, 'task_info'))

    # Сохраняем и закрываем
    conn.commit()
    conn.close()
