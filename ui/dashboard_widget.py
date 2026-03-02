"""
RES — ui/dashboard_widget.py
==============================
Workshop Kanban dashboard.

Displays all active vehicles organised in columns — one column per
active repair process. Each vehicle is shown as a VehicleCardWidget
with colour-coded elapsed/remaining time.

Features:
  - Auto-refreshes every 30 seconds via QTimer
  - Bay capacity indicators per column header
  - Vehicles grouped by current process
  - Click on a card → emits request to open Vehicle Detail view
"""

from collections import defaultdict
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QSizePolicy,
    QMenu,
)
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QTimer

from core.process_engine import get_active_processes, get_all_active_vehicle_logs
from core.capacity_tracker import CapacityTracker
from ui.vehicle_card_widget import VehicleCardWidget
from ui.dialogs.register_vehicle_dialog import RegisterVehicleDialog


# Auto-refresh interval in milliseconds (30 seconds)
REFRESH_INTERVAL_MS = 30_000


class DashboardWidget(QWidget):
    """
    The main workshop Kanban dashboard.

    Shows one scrollable column per repair process, populated with
    VehicleCardWidget instances for each active vehicle.
    Auto-refreshes every 30 seconds.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialise the dashboard and start the auto-refresh timer."""
        super().__init__(parent)
        self._capacity_tracker = CapacityTracker()
        self._build_ui()
        self.refresh()

        # Auto-refresh every 30 seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(REFRESH_INTERVAL_MS)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the outer layout with a header bar and scrollable Kanban area."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header ---
        header = QHBoxLayout()

        title = QLabel(self.tr("Workshop Dashboard"))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        # Add Vehicle button
        add_btn = QPushButton(self.tr("+ Add Vehicle"))
        add_btn.setFixedWidth(140)
        add_btn.clicked.connect(self._on_new_vehicle)
        header.addWidget(add_btn)

        refresh_btn = QPushButton(self.tr("↻  Refresh"))
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(110)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        outer.addLayout(header)

        # --- Scrollable Kanban area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        self._kanban_container = QWidget()
        self._kanban_layout = QHBoxLayout(self._kanban_container)
        self._kanban_layout.setContentsMargins(0, 0, 0, 0)
        self._kanban_layout.setSpacing(12)
        self._kanban_layout.addStretch()   # Right-side stretch (pushes columns left)

        scroll.setWidget(self._kanban_container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Data Refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Reload all data from the database and rebuild the Kanban board.

        Called automatically every 30 seconds and on manual refresh button.
        Clears all existing column widgets and rebuilds from scratch to
        ensure consistency with the database state.
        """
        self._capacity_tracker.refresh()

        # Clear existing columns (except the trailing stretch)
        while self._kanban_layout.count() > 1:
            item = self._kanban_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load data
        processes = get_active_processes()
        active_logs = get_all_active_vehicle_logs()

        # Group vehicle logs by process_id
        logs_by_process: dict[int, list[dict]] = defaultdict(list)
        for log in active_logs:
            logs_by_process[log["process_id"]].append(log)

        # Build one column per process
        for process in processes:
            col = self._build_process_column(
                process, logs_by_process.get(process.id, [])
            )
            self._kanban_layout.insertWidget(
                self._kanban_layout.count() - 1, col
            )

    # ------------------------------------------------------------------
    # Column builder
    # ------------------------------------------------------------------

    def _build_process_column(
        self, process, vehicle_logs: list[dict]
    ) -> QWidget:
        """
        Build a single Kanban column for a repair process.

        Args:
            process:      The Process ORM object.
            vehicle_logs: List of active vehicle dicts for this process.

        Returns:
            A styled QWidget representing the column.
        """
        column = QWidget()
        column.setFixedWidth(220)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(8)

        # --- Column header ---
        header = QFrame()
        header.setObjectName("columnHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(2)

        name_label = QLabel(process.name)
        name_label.setObjectName("columnHeader")
        header_layout.addWidget(name_label)

        # Capacity badge
        bay_info = self._capacity_tracker.get_bay_info(process.id)
        if bay_info:
            current = bay_info["current"]
            maximum = bay_info["max"]
            badge = QLabel(f"{current}/{maximum}")
            badge.setObjectName("capacityBadge")
            badge.setProperty("full", str(bay_info["is_full"]).lower())
            badge.setAlignment(Qt.AlignRight)
            header_layout.addWidget(badge)

        column_layout.addWidget(header)

        # --- Vehicle cards ---
        if vehicle_logs:
            for log_data in vehicle_logs:
                card = VehicleCardWidget(log_data)
                card.card_clicked.connect(self._on_card_clicked)
                column_layout.addWidget(card)
        else:
            # Empty state
            empty = QLabel(self.tr("No vehicles"))
            empty.setObjectName("subtitle")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("padding: 20px 0;")
            column_layout.addWidget(empty)

        column_layout.addStretch()
        return column

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_new_vehicle(self) -> None:
        """
        Open the Register Vehicle dialog and refresh the dashboard
        if registration was successful.
        """
        dlg = RegisterVehicleDialog(self)
        if dlg.exec():
            # If the user clicked 'Register & Check In' and it succeeded
            self.refresh()
            print(f"[Dashboard] New vehicle registered: id={dlg.new_vehicle_id}")

    def _on_card_clicked(self, vehicle_id: int, process_id: int) -> None:
        """
        Handle a vehicle card click by showing a context menu.

        The menu offers actions that make sense for the current phase:
        - Report Finding (opens FindingsDialog)
        - Roll Back Vehicle (opens RollbackDialog)

        Args:
            vehicle_id: The ID of the clicked vehicle.
            process_id: The ID of the process the vehicle is currently in.
        """
        menu = QMenu(self)
        report_act = menu.addAction(self.tr("Report Finding"))
        rollback_act = menu.addAction(self.tr("Roll Back"))
        action = menu.exec(QCursor.pos())

        if action == report_act:
            # determine active log id
            from core.process_engine import get_active_log
            log = get_active_log(vehicle_id, process_id)
            log_id = log.id if log else None
            from ui.findings_dialog import FindingsDialog

            dlg = FindingsDialog(vehicle_id=vehicle_id, process_log_id=log_id, parent=self)
            if dlg.exec():
                # refresh dashboard after reporting
                self.refresh()
                print(f"[Dashboard] Finding reported for vehicle {vehicle_id}")

        elif action == rollback_act:
            from ui.rollback_dialog import RollbackDialog

            dlg = RollbackDialog(vehicle_id=vehicle_id, current_process_id=process_id, parent=self)
            if dlg.exec():
                self.refresh()
                print(f"[Dashboard] Vehicle {vehicle_id} rolled back")
