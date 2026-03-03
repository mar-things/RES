"""
RES — ui/vehicle_card_widget.py
==================================
A compact card widget representing one vehicle's status in the dashboard.

Displays:
  - License plate and vehicle name
  - Elapsed time (green/amber/red)
  - Remaining time estimate
  - Assigned staff name
  - Check-in timestamp

The card's left border color reflects time status:
  Green  = on time (remaining > 20% of estimate)
  Amber  = near deadline
  Red    = overdue
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, Signal

from core.time_tracker import format_duration


class VehicleCardWidget(QFrame):
    """
    A card widget for a single active vehicle in a process bay.

    Signals:
        card_clicked: Emitted when the card is clicked.
                      Carries the vehicle_id and process_id (int, int).
    """
    
    card_clicked = Signal(int, int)

    def __init__(
        self,
        vehicle_data: dict,
        parent: Optional[QFrame] = None,
    ) -> None:
        """Initialize the card with a data dictionary.

        Args:
            vehicle_data: Dict from process_engine.get_all_active_vehicle_logs().
                          Keys: vehicle_id, plate, make, model, process_name,
                                checkin_time, elapsed_minutes, remaining_minutes,
                                status, color.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setObjectName("vehicleCard")
        self.setCursor(Qt.PointingHandCursor)
        self._data = vehicle_data
        self.setProperty("color", vehicle_data.get("color", "green"))
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the card layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        d = self._data

        # --- Top row: plate + status pill ---
        top = QHBoxLayout()
        plate_label = QLabel(d.get("plate", "???"))
        plate_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top.addWidget(plate_label)
        top.addStretch()

        status_pill = QLabel(self._status_text(d.get("status", "")))
        status_pill.setObjectName("statusPill")
        status_pill.setProperty("status", d.get("status", ""))
        top.addWidget(status_pill)
        layout.addLayout(top)

        # --- Vehicle name ---
        name = QLabel(f"{d.get('make','')} {d.get('model','')}")
        name.setObjectName("subtitle")
        layout.addWidget(name)

        # --- Time row ---
        time_row = QHBoxLayout()

        elapsed = d.get("elapsed_minutes", 0.0)
        elapsed_label = QLabel(f"⏱ {format_duration(elapsed)}")
        elapsed_label.setStyleSheet(
            f"color: {self._color_hex(d.get('color','green'))}; font-weight: bold;"
        )
        time_row.addWidget(elapsed_label)
        time_row.addStretch()

        rem = d.get("remaining_minutes")
        if rem is not None:
            rem_text = self.tr("Overdue") if rem < 0 else f"{format_duration(rem)} {self.tr('left')}"
            rem_label = QLabel(rem_text)
            rem_label.setObjectName("subtitle")
            time_row.addWidget(rem_label)

        layout.addLayout(time_row)

        # --- Check-in time ---
        checkin: Optional[datetime] = d.get("checkin_time")
        if checkin:
            checkin_str = checkin.strftime("%H:%M")
            ci_label = QLabel(f"{self.tr('In since')} {checkin_str}")
            ci_label.setObjectName("subtitle")
            layout.addWidget(ci_label)

    def mousePressEvent(self, event) -> None:
        """Emit card_clicked with the vehicle_id and process_id when the card is clicked."""
        self.card_clicked.emit(
            self._data.get("vehicle_id", -1),
            self._data.get("process_id", -1),
        )
        super().mousePressEvent(event)

    def update_data(self, vehicle_data: dict) -> None:
        """
        Refresh the card with updated vehicle data.

        Used by the dashboard auto-refresh (every 30 seconds).

        Args:
            vehicle_data: Updated data dict from process_engine.
        """
        self._data = vehicle_data
        self.setProperty("color", vehicle_data.get("color", "green"))
        # Rebuild UI with fresh data
        for child in self.findChildren(QLabel):
            child.deleteLater()
        self._build_ui()
        self.style().unpolish(self)
        self.style().polish(self)

    @staticmethod
    def _status_text(status: str) -> str:
        """Convert a status code to a display label."""
        return {
            "in_progress": "In Progress",
            "waiting": "Waiting",
            "completed": "Completed",
        }.get(status, status.replace("_", " ").title())

    @staticmethod
    def _color_hex(color: str) -> str:
        """Map color name to hex code for inline styling."""
        return {
            "green": "#22c55e",
            "amber": "#f59e0b",
            "red":   "#ef4444",
        }.get(color, "#9aa0b4")
