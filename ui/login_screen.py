"""
RES — ui/login_screen.py
==========================
Login screen widget.

Shown at application startup before any other views.
Emits login_successful signal on successful authentication,
which causes main_window to replace this widget with the full UI.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from services.auth_service import login


class LoginScreen(QWidget):
    """
    Full-window login form.

    Signals:
        login_successful: Emitted when authentication succeeds.
                          MainWindow connects to this to swap views.
    """

    login_successful = Signal()

    def __init__(self) -> None:
        """Build the login screen UI."""
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        """Centre a card-style login form on the screen."""
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        # Card container
        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        # Title
        title = QLabel("RES")
        title.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title.setStyleSheet("color: #2563eb;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel(self.tr("Repair Execution System"))
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(sub)

        card_layout.addSpacing(16)

        # Username
        card_layout.addWidget(QLabel(self.tr("Username")))
        self._username = QLineEdit()
        self._username.setPlaceholderText(self.tr("Enter username"))
        self._username.setFixedHeight(38)
        card_layout.addWidget(self._username)

        # Password
        card_layout.addWidget(QLabel(self.tr("Password")))
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText(self.tr("Enter password"))
        self._password.setFixedHeight(38)
        self._password.returnPressed.connect(self._attempt_login)
        card_layout.addWidget(self._password)

        # Error label (hidden by default)
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.setVisible(False)
        card_layout.addWidget(self._error_label)

        # Login button
        self._login_btn = QPushButton(self.tr("Sign In"))
        self._login_btn.setFixedHeight(40)
        self._login_btn.clicked.connect(self._attempt_login)
        card_layout.addWidget(self._login_btn)

        outer.addWidget(card)

    def _attempt_login(self) -> None:
        """
        Validate credentials and emit login_successful on success.

        Shows an error message for invalid credentials without
        revealing whether username or password is wrong.
        """
        username = self._username.text().strip()
        password = self._password.text()

        user = login(username, password)
        if user:
            self.login_successful.emit()
        else:
            self._error_label.setText(self.tr("Invalid username or password."))
            self._error_label.setVisible(True)
            self._password.clear()
            self._password.setFocus()
