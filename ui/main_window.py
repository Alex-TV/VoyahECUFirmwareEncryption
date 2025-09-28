from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QFrame, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
from ui.encryption_tab import EncryptionTab
from ui.decryption_tab import DecryptionTab
from ui.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Firmware Encryptor')
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(150)
        sidebar.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)

        self.sidebar_list = QListWidget()
        self.sidebar_list.addItem("Encryption")
        self.sidebar_list.addItem("Decryption")
        self.sidebar_list.addItem("Settings")
        self.sidebar_list.setFrameShape(QFrame.NoFrame)
        self.sidebar_list.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ccc;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        self.sidebar_list.currentRowChanged.connect(self.on_sidebar_change)

        sidebar_layout.addWidget(self.sidebar_list)
        sidebar.setLayout(sidebar_layout)

        # Right content
        self.content_stack = EncryptionTab()  # Default

        # Add to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack)

        central_widget.setLayout(main_layout)

    def on_sidebar_change(self, index):
        if index == 0:
            self.content_stack.setParent(None)
            self.content_stack = EncryptionTab()
        elif index == 1:
            self.content_stack.setParent(None)
            self.content_stack = DecryptionTab()
        elif index == 2:
            self.content_stack.setParent(None)
            self.content_stack = SettingsTab()

        self.centralWidget().layout().removeWidget(self.centralWidget().findChild(QWidget, "content"))
        self.centralWidget().layout().addWidget(self.content_stack)