"""
RES — ui/dialogs/register_vehicle_dialog.py
=============================================
Multi-section dialog for registering a new vehicle.

Layout:
  ┌─ Customer Information ──────────────────────────┐
  │  Name, Phone (WhatsApp), Email, ID              │
  ├─ Vehicle Information ───────────────────────────┤
  │  Plate, Make, Model, Year, Color, VIN            │
  │  Crash Severity (LOW / HIGH)                    │
  ├─ Insurance (optional) ─────────────────────────┤
  │  Company, Claim number, Budget estimate         │
  └─────────────────────────────────────────────────┘
  [Cancel]                    [Register & Check In]

On success the dialog returns the new vehicle_id so the
dashboard can refresh and highlight the new card.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QPushButton, QFrame,
    QRadioButton, QButtonGroup, QMessageBox, QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIntValidator

from services.vehicle_service import register_vehicle, list_insurance_companies


class RegisterVehicleDialog(QDialog):
    """
    Dialog for registering a new vehicle and checking it into Reception.

    After the user fills in the form and clicks "Register & Check In",
    the vehicle is persisted and checked into the first process.

    Attributes:
        new_vehicle_id (int | None): ID of the created vehicle, set on
            success, used by the caller to refresh the dashboard.
    """

    def __init__(self, parent=None) -> None:
        """Build the registration form."""
        super().__init__(parent)
        self.setWindowTitle(self.tr("Register New Vehicle"))
        self.setMinimumWidth(540)
        self.setModal(True)
        self.new_vehicle_id: Optional[int] = None
        self._insurance_data: list = []
        self._build_ui()
        self._load_insurance_companies()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build and arrange the form sections."""
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(20, 20, 20, 20)

        # Scrollable form area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(0, 0, 12, 0)

        form_layout.addWidget(self._build_customer_section())
        form_layout.addWidget(self._build_vehicle_section())
        form_layout.addWidget(self._build_insurance_section())
        form_layout.addStretch()

        scroll.setWidget(form_widget)
        root.addWidget(scroll)

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

        self._submit_btn = QPushButton(self.tr("✔  Register & Check In"))
        self._submit_btn.setFixedWidth(200)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self._submit_btn)

        root.addLayout(btn_row)

    def _build_customer_section(self) -> QGroupBox:
        """Build the Customer Information section."""
        group = QGroupBox(self.tr("Customer Information"))
        layout = QFormLayout(group)
        layout.setSpacing(10)

        self._customer_name = QLineEdit()
        self._customer_name.setPlaceholderText(self.tr("Full name"))
        layout.addRow(self.tr("Name *"), self._customer_name)

        self._customer_phone = QLineEdit()
        self._customer_phone.setPlaceholderText("+1234567890")
        layout.addRow(self.tr("WhatsApp Phone *"), self._customer_phone)

        self._customer_email = QLineEdit()
        self._customer_email.setPlaceholderText(self.tr("Optional"))
        layout.addRow(self.tr("Email"), self._customer_email)

        self._customer_id = QLineEdit()
        self._customer_id.setPlaceholderText(self.tr("Passport / ID number"))
        layout.addRow(self.tr("ID Document"), self._customer_id)

        return group

    def _build_vehicle_section(self) -> QGroupBox:
        """Build the Vehicle Information section."""
        group = QGroupBox(self.tr("Vehicle Information"))
        layout = QFormLayout(group)
        layout.setSpacing(10)

        # License plate
        self._plate = QLineEdit()
        self._plate.setPlaceholderText("ABC-1234")
        self._plate.setMaxLength(20)
        layout.addRow(self.tr("License Plate *"), self._plate)

        # Make / Model in one row
        mm_row = QHBoxLayout()
        self._make = QLineEdit()
        self._make.setPlaceholderText(self.tr("Make (Toyota)"))
        self._model = QLineEdit()
        self._model.setPlaceholderText(self.tr("Model (Corolla)"))
        mm_row.addWidget(self._make)
        mm_row.addWidget(self._model)
        layout.addRow(self.tr("Make / Model *"), mm_row)

        # Year / Color in one row
        yc_row = QHBoxLayout()
        self._year = QSpinBox()
        self._year.setRange(1960, 2030)
        self._year.setValue(2020)
        self._color = QLineEdit()
        self._color.setPlaceholderText(self.tr("Color"))
        yc_row.addWidget(self._year)
        yc_row.addWidget(self._color)
        layout.addRow(self.tr("Year / Color"), yc_row)

        # VIN
        self._vin = QLineEdit()
        self._vin.setPlaceholderText(self.tr("Optional — 17 chars"))
        self._vin.setMaxLength(17)
        layout.addRow(self.tr("VIN / Chassis"), self._vin)

        # Crash severity
        sev_row = QHBoxLayout()
        self._sev_group = QButtonGroup(self)
        self._sev_low = QRadioButton(self.tr("LOW — minor damage (skips Mechanic step)"))
        self._sev_high = QRadioButton(self.tr("HIGH — major damage (full pipeline)"))
        self._sev_low.setChecked(True)
        self._sev_group.addButton(self._sev_low)
        self._sev_group.addButton(self._sev_high)
        sev_col = QVBoxLayout()
        sev_col.addWidget(self._sev_low)
        sev_col.addWidget(self._sev_high)
        layout.addRow(self.tr("Crash Severity *"), sev_col)

        # Notes
        self._notes = QTextEdit()
        self._notes.setPlaceholderText(self.tr("Intake notes, visible damage description..."))
        self._notes.setFixedHeight(70)
        layout.addRow(self.tr("Intake Notes"), self._notes)

        return group

    def _build_insurance_section(self) -> QGroupBox:
        """Build the Insurance (optional) section."""
        group = QGroupBox(self.tr("Insurance (Optional)"))
        layout = QFormLayout(group)
        layout.setSpacing(10)

        self._insurance_combo = QComboBox()
        self._insurance_combo.addItem(self.tr("— None / Private Pay —"), None)
        layout.addRow(self.tr("Insurance Company"), self._insurance_combo)

        self._claim_number = QLineEdit()
        self._claim_number.setPlaceholderText(self.tr("Claim / policy number"))
        layout.addRow(self.tr("Claim Number"), self._claim_number)

        self._budget = QDoubleSpinBox()
        self._budget.setRange(0.0, 999_999.99)
        self._budget.setPrefix("$")
        self._budget.setDecimals(2)
        self._budget.setValue(0.0)
        layout.addRow(self.tr("Estimated Budget"), self._budget)

        return group

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_insurance_companies(self) -> None:
        """Populate the insurance company combo box from the database."""
        try:
            companies = list_insurance_companies()
            self._insurance_data = companies
            for c in companies:
                self._insurance_combo.addItem(c.name, c.id)
        except Exception as exc:
            print(f"[RegisterDialog] Could not load insurance companies: {exc}")

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def _on_submit(self) -> None:
        """
        Validate fields, register the vehicle, and accept the dialog.

        Shows inline errors for missing required fields. On success, sets
        self.new_vehicle_id and calls self.accept() so the caller
        can refresh the dashboard.
        """
        self._error_label.setVisible(False)

        # Basic validation
        name   = self._customer_name.text().strip()
        phone  = self._customer_phone.text().strip()
        plate  = self._plate.text().strip()
        make   = self._make.text().strip()
        model  = self._model.text().strip()

        missing = []
        if not name:   missing.append(self.tr("Customer name"))
        if not phone:  missing.append(self.tr("WhatsApp phone"))
        if not plate:  missing.append(self.tr("License plate"))
        if not make:   missing.append(self.tr("Make"))
        if not model:  missing.append(self.tr("Model"))

        if missing:
            self._error_label.setText(
                self.tr("Required: ") + ", ".join(missing)
            )
            self._error_label.setVisible(True)
            return

        # Collect optional / nullable values
        year  = self._year.value() if self._year.value() >= 1960 else None
        color = self._color.text().strip() or None
        vin   = self._vin.text().strip() or None
        email = self._customer_email.text().strip() or None
        id_doc = self._customer_id.text().strip() or None
        claim  = self._claim_number.text().strip() or None
        budget = self._budget.value() if self._budget.value() > 0 else None
        severity = "HIGH" if self._sev_high.isChecked() else "LOW"
        insurance_id = self._insurance_combo.currentData()
        notes = self._notes.toPlainText().strip() or None

        try:
            self._submit_btn.setEnabled(False)
            self._submit_btn.setText(self.tr("Registering..."))

            vehicle_id, log = register_vehicle(
                customer_name=name,
                customer_phone=phone,
                customer_email=email,
                customer_id_doc=id_doc,
                license_plate=plate,
                make=make,
                model=model,
                year=year,
                color=color,
                vin=vin,
                crash_severity=severity,
                insurance_company_id=insurance_id,
                claim_number=claim,
                estimated_total_cost=budget,
                notes=notes,
            )
            self.new_vehicle_id = vehicle_id
            self.accept()

        except Exception as exc:
            self._submit_btn.setEnabled(True)
            self._submit_btn.setText(self.tr("✔  Register & Check In"))
            self._error_label.setText(str(exc))
            self._error_label.setVisible(True)
