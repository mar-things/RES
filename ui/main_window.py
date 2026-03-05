"""
RES — ui/main_window.py
=========================
Application main window and navigation shell.

Contains:
  - The top-level QMainWindow with a sidebar navigation
  - Role-based view switching (mechanics see fewer options)
  - A stacked widget that holds each functional view
  - Language switch action in the menu bar
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from services.auth_service import get_current_user, logout, has_role
from ui.dashboard_widget import DashboardWidget
from ui.login_screen import LoginScreen
from ui.insurance_dashboard import InsuranceDashboard


class PlaceholderWidget(QWidget):
    """
    A simple centered message for features still under development.
    """

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 24, QFont.Bold))
        t.setStyleSheet("color: #3b82f6;")
        t.setAlignment(Qt.AlignCenter)
        layout.addWidget(t)

        sub = QLabel(subtitle)
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)


class MainWindow(QMainWindow):
    """
    The application shell window.

    Contains a sidebar for navigation and a page stack for views.
    Role-based access control is enforced by hiding/disabling
    navigation items that the current user's role cannot access.

    The window starts on the login screen. After successful login,
    it switches to the main dashboard and builds the navigation.
    """

    def __init__(self) -> None:
        """Initialise the main window and show the login screen."""
        super().__init__()
        self.setWindowTitle(self.tr("RES — Repair Execution System"))
        self.resize(1400, 860)
        self.setMinimumSize(1100, 700)

        self._build_login_ui()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def _build_login_ui(self) -> None:
        """Show only the login screen (no navigation sidebar)."""
        self._login_screen = LoginScreen()
        self._login_screen.login_successful.connect(self._on_login_success)
        self.setCentralWidget(self._login_screen)

    def _on_login_success(self) -> None:
        """
        Called when the user logs in successfully.

        Replaces the login screen with the full navigation shell.
        """
        self._build_main_ui()

    # ------------------------------------------------------------------
    # Main shell
    # ------------------------------------------------------------------

    def _build_main_ui(self) -> None:
        """
        Build the navigation sidebar + page stack.

        Called once after a successful login. The layout is:
            [Sidebar | Main Content Area]
        """
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Left sidebar
        self._sidebar = self._build_sidebar()
        root_layout.addWidget(self._sidebar)

        # Page stack (right side)
        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack)

        # Register pages
        self._dashboard = DashboardWidget()
        self._stack.addWidget(self._dashboard)

        # Index 1: Vehicle Detail (Phase 1+)
        self._stack.addWidget(PlaceholderWidget(
            self.tr("Vehicle Detail View"),
            self.tr("Phase 2: Full vehicle history, findings, and process controls.")
        ))

        # Index 2: Insurance Dashboard (Phase 3)
        self._stack.addWidget(InsuranceDashboard())

        # Index 3: Reports (Phase 4)
        self._stack.addWidget(PlaceholderWidget(
            self.tr("Advanced Analytics"),
            self.tr("Phase 4: Transit time, efficiency, and cost reporting.")
        ))

        # Index 4: Settings / Admin (Phase 6)
        self._stack.addWidget(PlaceholderWidget(
            self.tr("System Settings"),
            self.tr("Phase 6: User management, language, and theme config.")
        ))

        self._stack.setCurrentIndex(0)
        self.setCentralWidget(central)

        # Apply role visibility to nav buttons
        self._apply_role_visibility()

        # Update window title with username
        user = get_current_user()
        if user:
            self.setWindowTitle(
                f"RES — {self.tr('Repair Execution System')} [{user.full_name}]"
            )

    def _build_sidebar(self) -> QWidget:
        """
        Build the left navigation sidebar.

        Returns:
            A QWidget configured as the sidebar with nav buttons.
        """
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # Application logo / name
        logo = QLabel("RES")
        logo.setFont(QFont("Segoe UI", 22, QFont.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("color: #2563eb; margin-bottom: 8px;")
        layout.addWidget(logo)

        subtitle = QLabel(self.tr("Workshop Manager"))
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #2a2d3a; margin: 12px 0;")
        layout.addWidget(sep)

        # Navigation buttons
        self._nav_dashboard = self._nav_button(self.tr("📋  Dashboard"), 0)
        self._nav_insurance = self._nav_button(self.tr("🏢  Insurance"), 2)
        self._nav_reports = self._nav_button(self.tr("📊  Reports"), 3)
        self._nav_settings = self._nav_button(self.tr("⚙️  Settings"), 4)

        layout.addWidget(self._nav_dashboard)
        layout.addWidget(self._nav_insurance)
        layout.addWidget(self._nav_reports)
        layout.addWidget(self._nav_settings)
        layout.addStretch()

        # Logged-in user info
        user = get_current_user()
        if user:
            user_label = QLabel(f"👤 {user.full_name}\n{user.role}")
            user_label.setObjectName("subtitle")
            user_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(user_label)

        # Logout button
        logout_btn = QPushButton(self.tr("Logout"))
        logout_btn.setObjectName("secondaryButton")
        logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(logout_btn)

        self._set_active_nav(0)  # Default to dashboard
        return sidebar

    def _nav_button(self, label: str, page_index: int) -> QPushButton:
        """
        Create a sidebar navigation button.

        Args:
            label:      Button text.
            page_index: Index of the page in QStackedWidget to switch to.

        Returns:
            A styled QPushButton connected to switch pages.
        """
        btn = QPushButton(label)
        btn.setFixedHeight(42)
        btn.clicked.connect(lambda: self._navigate_to(page_index))
        return btn

    def _navigate_to(self, index: int) -> None:
        """
        Switch the main content area to the specified page index.

        Args:
            index: Index in the QStackedWidget.
        """
        self._stack.setCurrentIndex(index)
        self._set_active_nav(index)

    def _set_active_nav(self, active_index: int) -> None:
        """
        Highlight the active navigation button.

        Args:
            active_index: The page index of the currently active view.
        """
        nav_map = {
            0: self._nav_dashboard,
            2: self._nav_insurance,
            3: self._nav_reports,
            4: self._nav_settings,
        }
        for idx, btn in nav_map.items():
            btn.setProperty("active", str(idx == active_index).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _apply_role_visibility(self) -> None:
        """
        Show or hide nav items based on the current user's role.

        insurance-viewer: sees only the Insurance dashboard.
        mechanic:         sees Dashboard only.
        manager/admin:    sees everything.
        """
        is_admin_or_manager = has_role("admin", "manager")
        is_insurance = has_role("insurance-viewer")

        self._nav_insurance.setVisible(is_admin_or_manager or is_insurance)
        self._nav_reports.setVisible(is_admin_or_manager)
        self._nav_settings.setVisible(has_role("admin"))

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def _on_logout(self) -> None:
        """Log out the current user and return to the login screen."""
        logout()
        self._build_login_ui()
