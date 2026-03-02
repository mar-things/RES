"""
RES — ui/insurance_dashboard.py
=================================
Widget shown to users with the `insurance-viewer` role. Operators at
an insurance company use this interface to acknowledge and approve
findings reported by the workshop.

The dashboard is scoped to the insurer associated with the logged-in
user; vehicles belonging to other companies are never visible.

Features implemented in Phase 3 step 1:

* Table of pending findings (description, cost, vehicle, process,
  reported timestamp).
* Action buttons for Acknowledge / Approve / Reject.
* Simple KPI banner showing count of pending findings.
* Automatic refresh when actions are performed.

Later phases will add SLA metrics, historical data, and more analytics.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox,
)
from PySide6.QtCore import Qt

from services.auth_service import get_current_user, require_role
from services.findings_service import (
    list_pending_for_insurer,
    acknowledge_finding,
    approve_finding,
    reject_finding,
)


class InsuranceDashboard(QWidget):
    """Insurance company dashboard for tracking pending findings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._user = get_current_user()
        require_role("insurance-viewer", "admin", "manager")
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        self._kpi_label = QLabel()
        self._kpi_label.setObjectName("sectionTitle")
        root.addWidget(self._kpi_label)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID",
            "Vehicle",
            "Process",
            "Reported At",
            "Description",
            "Cost",
            "Actions",
        ])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setColumnHidden(0, True)  # hide ID column
        root.addWidget(self._table)

    # ------------------------------------------------------------------
    # Data management
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload pending findings from the database and update the table."""
        if not self._user or not self._user.insurance_company_id:
            self._kpi_label.setText(self.tr("No insurer linked to this user."))
            self._table.setRowCount(0)
            return

        findings = list_pending_for_insurer(self._user.insurance_company_id)
        self._kpi_label.setText(
            self.tr("Pending findings: {count}").format(count=len(findings))
        )

        self._table.setRowCount(len(findings))
        for row, f in enumerate(findings):
            vehicle_plate = f.vehicle.license_plate if f.vehicle else ""
            process_name = f.process_log.process.name if f.process_log and f.process_log.process else ""
            reported = f.reported_at.strftime("%Y-%m-%d %H:%M") if f.reported_at else ""

            self._table.setItem(row, 0, QTableWidgetItem(str(f.id)))
            self._table.setItem(row, 1, QTableWidgetItem(vehicle_plate))
            self._table.setItem(row, 2, QTableWidgetItem(process_name))
            self._table.setItem(row, 3, QTableWidgetItem(reported))
            self._table.setItem(row, 4, QTableWidgetItem(f.description))
            self._table.setItem(row, 5, QTableWidgetItem(f"${f.additional_cost:.2f}"))

            # actions: acknowledge + approve + reject
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)

            ack_btn = QPushButton(self.tr("Acknowledge"))
            ack_btn.setFixedWidth(90)
            ack_btn.clicked.connect(lambda _, fid=f.id: self._on_ack(fid))
            action_layout.addWidget(ack_btn)

            appr_btn = QPushButton(self.tr("Approve"))
            appr_btn.setFixedWidth(80)
            appr_btn.clicked.connect(lambda _, fid=f.id: self._on_approve(fid))
            action_layout.addWidget(appr_btn)

            rej_btn = QPushButton(self.tr("Reject"))
            rej_btn.setFixedWidth(70)
            rej_btn.clicked.connect(lambda _, fid=f.id: self._on_reject(fid))
            action_layout.addWidget(rej_btn)

            action_layout.addStretch()
            self._table.setCellWidget(row, 6, action_widget)

        self._table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Action callbacks
    # ------------------------------------------------------------------

    def _on_ack(self, finding_id: int) -> None:
        try:
            acknowledge_finding(finding_id)
            QMessageBox.information(self, self.tr("Acknowledged"),
                                    self.tr("Finding has been acknowledged."))
        except Exception as exc:
            QMessageBox.warning(self, self.tr("Error"), str(exc))
        finally:
            self.refresh()

    def _on_approve(self, finding_id: int) -> None:
        try:
            approve_finding(finding_id, approved_by_name=self._user.full_name)
            QMessageBox.information(self, self.tr("Approved"),
                                    self.tr("Finding budget approved."))
        except Exception as exc:
            QMessageBox.warning(self, self.tr("Error"), str(exc))
        finally:
            self.refresh()

    def _on_reject(self, finding_id: int) -> None:
        ans = QMessageBox.question(
            self,
            self.tr("Reject Finding"),
            self.tr("Are you sure you want to reject this finding?"),
        )
        if ans == QMessageBox.Yes:
            try:
                reject_finding(finding_id, rejected_by_name=self._user.full_name)
                QMessageBox.information(self, self.tr("Rejected"),
                                        self.tr("Finding has been rejected."))
            except Exception as exc:
                QMessageBox.warning(self, self.tr("Error"), str(exc))
            finally:
                self.refresh()
