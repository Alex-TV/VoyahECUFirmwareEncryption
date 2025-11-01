from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QMessageBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt
from core.context_updater import update_context_db, clear_context_db
from core.settings_manager import SettingsManager

class ContextTab(QWidget):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self.context_path = None
        self.context_file_path = None
        self.init_ui()
        self.load_paths_from_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("🧠 Context:")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(20)

        # info_label = QLabel("This is a placeholder for the Context Tab. You can add relevant widgets and functionality here.")
        # info_label.setWordWrap(True)
        # info_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(info_label)

        # Context file selection
        context_layout = QHBoxLayout()
        self.context_path = QLineEdit()
        context_btn = QPushButton('Select Context File')
        context_btn.clicked.connect(self.select_context_file)
        context_layout.addWidget(QLabel('DB File:'))
        context_layout.addWidget(self.context_path)
        context_layout.addWidget(context_btn)
        layout.addLayout(context_layout)

        fill_group_box = QGroupBox("🧰 Fill")
        fill_layout = QVBoxLayout()

        # Buttons
        update_by_firmware_info_btn = QPushButton('Update by firmware_info.json')
        update_by_firmware_info_btn.clicked.connect(self.update_context)
        fill_layout.addWidget(update_by_firmware_info_btn)

        fill_group_box.setLayout(fill_layout)
        layout.addWidget(fill_group_box)

        layout.addSpacing(20)

        cleaning_group_box = QGroupBox("🧹 Cleaning")
        inner_layout = QVBoxLayout()
        # Горизонтальный макет для имени и поля ввода
        input_layout = QHBoxLayout()
        label = QLabel("Target baseline version:")
        self.line_edit = QLineEdit()
        self.line_edit.setMaxLength(20)
        self.line_edit.setPlaceholderText("Enter target baseline version...")

        input_layout.addWidget(label)
        input_layout.addWidget(self.line_edit)

        # Добавляем горизонтальный макет в основной вертикальный
        #layout.addLayout(input_layout)
        #roup_box.addLayout(input_layout)
        inner_layout.addLayout(input_layout)

        # Создаём QCheckBox
        self.checkbox = QCheckBox("Remove IVI entries")
        inner_layout.addWidget(self.checkbox)

        clear_btn = QPushButton('Clear')
        clear_btn.clicked.connect(self.clear_context)
        inner_layout.addWidget(clear_btn)

        cleaning_group_box.setLayout(inner_layout)

        layout.addWidget(cleaning_group_box)
        self.setLayout(layout)

    def select_context_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Context File', '', 'DB Files (*.db)')
        if file_path:
            self.context_path.setText(file_path)
            self.context_file_path = file_path
            self.settings.set_context_path(file_path)

    def update_context(self):
        if not self.context_file_path:
            QMessageBox.warning(self, 'Error', 'Please select a context DB file.')
            return
        try:
            ecus_pash = self.settings.get_output_path()
            update_context_db(self.context_file_path, ecus_pash)
            QMessageBox.information(self, 'Success', 'Context database updated successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to update context database:\n{str(e)}')

    def clear_context(self):
        if not self.context_file_path:
            QMessageBox.warning(self, 'Error', 'Please select a context DB file.')
            return
        try:
            baseline_version = self.line_edit.text().strip()
            if not baseline_version:
                QMessageBox.warning(self, 'Error', 'Please enter a target baseline version.')
                return
            clear_context_db(self.context_file_path, baseline_version, self.checkbox.isChecked())
            QMessageBox.information(self, 'Success', 'Context database clear successfully.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to clear context database:\n{str(e)}')

    def load_paths_from_settings(self):
        """Загружаем пути к файлам из настроек"""
        context_path = self.settings.get_context_path()

        if context_path:
            self.context_path.setText(context_path)
            self.context_file_path = context_path
