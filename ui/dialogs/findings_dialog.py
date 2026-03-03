"""
RES — ui/dialogs/findings_dialog.py
====================================
Dialog for recording a damage finding discovered during repair.

Mechanics use this when they spot additional work that was not
anticipated at intake. The form captures a description, an optional
additional cost estimate, and (for now) an optional photo path. A
placeholder "Use Cost Estimator" button is included for the future
Phase‑7 AI integration; it currently shows an informational tooltip
and is disabled.

Once the report is saved the system will notify the vehicle owner via
WhatsApp/SMS and the finding is stored with a timestamp so that the
insurance dashboard can track SLA metrics.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QDoubleSpinBox, QLineEdit, QPushButton, QFileDialog,
)
from PySide6.QtCore import Qt

from services.findings_service import report_finding as svc_report_finding


class FindingsDialog(QDialog):
    """Dialog used by workshop staff to log a new finding.

    Attributes:
        vehicle_id (int): The vehicle the finding belongs to.
        process_log_id (int): The active process log where the damage was
            discovered. Used for traceability.
        new_finding_id (int | None): Populated after successful report so
            callers can act on it if needed.
    """

    def __init__(
        self, vehicle_id: int, process_log_id: int, parent=None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Report Finding"))
        self.setModal(True)
        self.setMinimumWidth(480)

        self.vehicle_id = vehicle_id
        self.process_log_id = process_log_id
        self.new_finding_id: Optional[int] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        # Description
        desc_label = QLabel(self.tr("Description of damage *"))
        self._description = QTextEdit()
        self._description.setFixedHeight(100)
        self._description.setPlaceholderText(self.tr("Explain what was found on the vehicle..."))
        root.addWidget(desc_label)
        root.addWidget(self._description)

        # Additional cost
        cost_label = QLabel(self.tr("Estimated extra cost"))
        self._cost = QDoubleSpinBox()
        self._cost.setRange(0.0, 999_999.99)
        self._cost.setPrefix("$")
        self._cost.setDecimals(2)
        self._cost.setValue(0.0)
        root.addWidget(cost_label)
        root.addWidget(self._cost)

        # Photo path (optional)
        photo_label = QLabel(self.tr("Photo (optional)"))
        photo_row = QHBoxLayout()
        self._photo_path = QLineEdit()
        self._photo_path.setPlaceholderText(self.tr("Path to photo file"))
        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._on_browse)
        photo_row.addWidget(self._photo_path)
        photo_row.addWidget(browse_btn)
        root.addWidget(photo_label)
        root.addLayout(photo_row)

        # Cost estimator placeholder
        estimator_btn = QPushButton(self.tr("Use Cost Estimator"))
        estimator_btn.setEnabled(False)
        estimator_btn.setToolTip(self.tr("Coming in Phase 7 (AI integration)"))
        root.addWidget(estimator_btn)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef4444;")
        self._error_label.setVisible(False)
        root.addWidget(self._error_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setFixedWidth(120)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._submit_btn = QPushButton(self.tr("✔  Report"))
        self._submit_btn.setFixedWidth(120)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self._submit_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select photo"),
            "",
            self.tr("Image files (*.png *.jpg *.jpeg);;All files (*)"),
        )
        if path:
            self._photo_path.setText(path)

    def _on_submit(self) -> None:
        """Validate the form and call the service to record the finding."""
        self._error_label.setVisible(False)

        desc = self._description.toPlainText().strip()
        if not desc:
            self._error_label.setText(self.tr("Description is required."))
            self._error_label.setVisible(True)
            return

        cost = self._cost.value()
        photo = self._photo_path.text().strip() or None

        try:
            self._submit_btn.setEnabled(False)
            self._submit_btn.setText(self.tr("Reporting..."))

            finding = svc_report_finding(
                vehicle_id=self.vehicle_id,
                process_log_id=self.process_log_id,
                description=desc,
                additional_cost=cost,
                photo_path=photo,
            )
            self.new_finding_id = finding.id
            self.accept()

        except Exception as exc:
            self._submit_btn.setEnabled(True)
            self._submit_btn.setText(self.tr("✔  Report"))
            self._error_label.setText(str(exc))
            self._error_label.setVisible(True)
