"""
RES - ui/dialogs/rollback_dialog.py
====================================
Dialog for returning a vehicle to a prior repair process.

Managers and admins use this when rework is required. The dialog lists
only valid prior processes, requires a written reason, and delegates the
transactional rollback operation to the service layer.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from services.auth_service import get_current_user, require_role
from services.rollback_service import list_rollback_targets, rollback_vehicle


class RollbackDialog(QDialog):
    """
    Dialog used to approve and execute a vehicle rollback.

    Attributes:
        vehicle_id: Vehicle being rolled back.
        current_process_id: Process the vehicle is currently occupying.
        rollback_id: Created audit record ID after a successful rollback.
    """

    def __init__(
        self,
        vehicle_id: int,
        current_process_id: int,
        parent=None,
    ) -> None:
        """Build the rollback dialog and load valid target processes."""
        super().__init__(parent)
        require_role("manager", "admin")

        self.vehicle_id = vehicle_id
        self.current_process_id = current_process_id
        self.rollback_id: Optional[int] = None
        self._targets = []

        self.setWindowTitle(self.tr("Roll Back Vehicle"))
        self.setModal(True)
        self.setMinimumWidth(460)

        self._build_ui()
        self._load_targets()

    def _build_ui(self) -> None:
        """Build the form controls and action buttons."""
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel(self.tr("Return vehicle to a prior process"))
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        target_label = QLabel(self.tr("Target process *"))
        self._target_combo = QComboBox()
        root.addWidget(target_label)
        root.addWidget(self._target_combo)

        reason_label = QLabel(self.tr("Reason *"))
        self._reason = QTextEdit()
        self._reason.setFixedHeight(110)
        self._reason.setPlaceholderText(
            self.tr("Explain why this vehicle must return to an earlier process...")
        )
        root.addWidget(reason_label)
        root.addWidget(self._reason)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #ef4444;")
        self._error_label.setVisible(False)
        root.addWidget(self._error_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._submit_btn = QPushButton(self.tr("Approve Rollback"))
        self._submit_btn.setObjectName("dangerButton")
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self._submit_btn)

        root.addLayout(btn_row)

    def _load_targets(self) -> None:
        """Load valid prior processes into the target combo box."""
        try:
            self._targets = list_rollback_targets(self.vehicle_id)
            self._target_combo.clear()
            for process in self._targets:
                self._target_combo.addItem(process.name, process.id)

            if not self._targets:
                self._submit_btn.setEnabled(False)
                self._error_label.setText(
                    self.tr("No prior process is available for this vehicle.")
                )
                self._error_label.setVisible(True)
        except Exception as exc:
            self._submit_btn.setEnabled(False)
            self._error_label.setText(str(exc))
            self._error_label.setVisible(True)

    def _on_submit(self) -> None:
        """Validate the form, confirm the action, and perform the rollback."""
        self._error_label.setVisible(False)
        reason = self._reason.toPlainText().strip()
        to_process_id = self._target_combo.currentData()

        if not to_process_id:
            self._error_label.setText(self.tr("Select a target process."))
            self._error_label.setVisible(True)
            return
        if not reason:
            self._error_label.setText(self.tr("Rollback reason is required."))
            self._error_label.setVisible(True)
            return

        answer = QMessageBox.question(
            self,
            self.tr("Confirm Rollback"),
            self.tr("Approve this rollback and move the vehicle now?"),
        )
        if answer != QMessageBox.Yes:
            return

        user = get_current_user()
        if not user:
            self._error_label.setText(self.tr("You must be logged in."))
            self._error_label.setVisible(True)
            return

        try:
            self._submit_btn.setEnabled(False)
            self._submit_btn.setText(self.tr("Rolling back..."))
            rollback = rollback_vehicle(
                vehicle_id=self.vehicle_id,
                to_process_id=to_process_id,
                reason=reason,
                approved_by_id=user.id,
            )
            self.rollback_id = rollback.id
            self.accept()
        except Exception as exc:
            self._submit_btn.setEnabled(True)
            self._submit_btn.setText(self.tr("Approve Rollback"))
            self._error_label.setText(str(exc))
            self._error_label.setVisible(True)
