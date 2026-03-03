"""
RES — core/models.py
======================
All SQLAlchemy ORM models (database tables).

This is the single source of truth for the database schema.
All tables are defined here. To add a new table, add a new class
that inherits from Base (imported from core.database).

Design principles:
  - Soft deletes: records are never permanently deleted.
    Use is_deleted = True + deleted_at timestamp instead.
  - Full audit trail: every state change is timestamped.
  - All FK relationships use lazy="select" by default.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """Return the current UTC datetime (used as column server defaults)."""
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Users & Roles
# ---------------------------------------------------------------------------

class User(Base):
    """
    A staff member or insurance viewer who can log into the system.

    Roles:
        mechanic        — Can check in/out vehicles; report findings.
        manager         — All mechanic rights + approve rollbacks.
        admin           — Full access including user management.
        insurance-viewer — Read-only access to their company's vehicles.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)  # See docstring
    # For insurance-viewer role: which company they belong to
    insurance_company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("insurance_companies.id"), nullable=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    process_logs: Mapped[list["ProcessLog"]] = relationship(
        "ProcessLog", back_populates="assigned_user", foreign_keys="ProcessLog.assigned_user_id"
    )
    approved_rollbacks: Mapped[list["ProcessRollback"]] = relationship(
        "ProcessRollback", back_populates="approved_by_user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class Customer(Base):
    """
    A vehicle owner / client of the workshop.

    WhatsApp and SMS notifications are sent to phone_whatsapp.
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone_whatsapp: Mapped[str] = mapped_column(String(30), nullable=False)
    phone_alt: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    id_document: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.full_name!r}>"


# ---------------------------------------------------------------------------
# Insurance Companies
# ---------------------------------------------------------------------------

class InsuranceCompany(Base):
    """
    An insurance company whose clients bring vehicles to the workshop.

    Insurance company staff access the system via the Insurance Dashboard
    (role: insurance-viewer). They are NOT notified by WhatsApp/SMS;
    all their communication is through the dashboard.
    """
    __tablename__ = "insurance_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    adjuster_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="insurance_company")
    users: Mapped[list["User"]] = relationship("User", foreign_keys="User.insurance_company_id")

    def __repr__(self) -> str:
        return f"<InsuranceCompany id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------

class Vehicle(Base):
    """
    A vehicle brought in for crash repair.

    crash_severity drives the process routing:
        'LOW'  → Reception → Straightening → paint prep → ...
        'HIGH' → Reception → Mechanic → Straightening → paint prep → ...

    current_status tracks the vehicle's overall lifecycle stage:
        'reception', 'in_repair', 'qa', 'completed', 'delivered'
    """
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    make: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    vin: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id"), nullable=False
    )
    insurance_company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("insurance_companies.id"), nullable=True
    )

    # Insurance / claim info
    claim_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    crash_severity: Mapped[str] = mapped_column(
        String(10), nullable=False, default="LOW"
    )  # 'LOW' | 'HIGH'

    # Dates and status
    reception_date: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    current_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="reception"
    )

    # Cost tracking
    estimated_total_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    approved_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="vehicles")
    insurance_company: Mapped[Optional["InsuranceCompany"]] = relationship(
        "InsuranceCompany", back_populates="vehicles"
    )
    process_logs: Mapped[list["ProcessLog"]] = relationship(
        "ProcessLog", back_populates="vehicle"
    )
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="vehicle")
    rollbacks: Mapped[list["ProcessRollback"]] = relationship(
        "ProcessRollback", back_populates="vehicle"
    )
    parts_used: Mapped[list["RepairPartUsed"]] = relationship(
        "RepairPartUsed", back_populates="vehicle"
    )
    notifications: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog", back_populates="vehicle"
    )

    @property
    def display_name(self) -> str:
        """Short display string used on dashboard cards and kiosk."""
        return f"{self.license_plate} — {self.year} {self.make} {self.model}"

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} plate={self.license_plate!r}>"


# ---------------------------------------------------------------------------
# Process Definitions
# ---------------------------------------------------------------------------

class Process(Base):
    """
    A single step in the vehicle repair pipeline.

    The repair pipeline is driven entirely by this table — no process
    names or order are hardcoded in Python. To add a new process,
    insert a row here and set sequence_order accordingly.

    required_severity:
        None  → process applies to all vehicles (regardless of severity)
        'HIGH' → process only applies to high-severity vehicles (e.g. Mechanic)

    max_capacity:
        Maximum number of vehicles that can occupy this bay simultaneously.
        Used by CapacityTracker to flag capacity blocks vs. staff delays.
    """
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    std_hours_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    required_severity: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # None | 'HIGH'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    logs: Mapped[list["ProcessLog"]] = relationship("ProcessLog", back_populates="process")

    def __repr__(self) -> str:
        return f"<Process id={self.id} name={self.name!r} order={self.sequence_order}>"


# ---------------------------------------------------------------------------
# Process Logs (Check-in / Check-out)
# ---------------------------------------------------------------------------

class ProcessLog(Base):
    """
    Records a vehicle checking in and out of a single repair process.

    This is the primary source of truth for all time-based KPIs:
        - Actual time spent in each process
        - Comparison to estimated time
        - Source for cost analysis (time = cost)

    status values:
        'waiting'      — Checked in but bay is at capacity; vehicle queued.
        'in_progress'  — Actively being worked on.
        'completed'    — Checked out successfully.
        'rolled_back'  — This log was superseded by a rollback event.
    """
    __tablename__ = "process_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    process_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processes.id"), nullable=False
    )
    assigned_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Timestamps — core KPI data
    checkin_time: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    checkout_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Time tracking
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="process_logs")
    process: Mapped["Process"] = relationship("Process", back_populates="logs")
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="process_logs", foreign_keys=[assigned_user_id]
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="process_log"
    )
    # Transitions where this log is the source or destination
    transitions_from: Mapped[list["ProcessTransition"]] = relationship(
        "ProcessTransition",
        back_populates="from_log",
        foreign_keys="ProcessTransition.from_process_log_id",
    )
    transitions_to: Mapped[list["ProcessTransition"]] = relationship(
        "ProcessTransition",
        back_populates="to_log",
        foreign_keys="ProcessTransition.to_process_log_id",
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessLog id={self.id} vehicle={self.vehicle_id} "
            f"process={self.process_id} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# Process Transitions (Transit time between processes)
# ---------------------------------------------------------------------------

class ProcessTransition(Base):
    """
    Records the elapsed time between a vehicle checking out of one
    process and checking in to the next.

    transit_minutes is the key metric for workshop layout optimisation:
    long transit times may indicate inefficient bay layouts or staffing.

    delay_reason:
        'capacity' — Next bay was full; vehicle had to wait.
        'staff'    — Bay had capacity but vehicle was not moved promptly.
        None       — Transit was immediate or reason not captured.
    """
    __tablename__ = "process_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    from_process_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("process_logs.id"), nullable=False
    )
    to_process_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("process_logs.id"), nullable=False
    )
    transit_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delay_reason: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    from_log: Mapped["ProcessLog"] = relationship(
        "ProcessLog", back_populates="transitions_from",
        foreign_keys=[from_process_log_id]
    )
    to_log: Mapped["ProcessLog"] = relationship(
        "ProcessLog", back_populates="transitions_to",
        foreign_keys=[to_process_log_id]
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessTransition id={self.id} "
            f"from={self.from_process_log_id} to={self.to_process_log_id} "
            f"transit={self.transit_minutes}min>"
        )


# ---------------------------------------------------------------------------
# Process Rollbacks
# ---------------------------------------------------------------------------

class ProcessRollback(Base):
    """
    Records a vehicle being returned to a previously completed process.

    Rollbacks can target any prior process (not just the immediately
    previous one). This covers both mid-repair rework and QA failure.

    Every rollback requires:
        - A mandatory written reason
        - Approval from a manager or admin role
    Nothing is ever deleted — the full history is preserved.
    """
    __tablename__ = "process_rollbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    from_process_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processes.id"), nullable=False
    )
    to_process_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processes.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="rollbacks")
    from_process: Mapped["Process"] = relationship(
        "Process", foreign_keys=[from_process_id]
    )
    to_process: Mapped["Process"] = relationship(
        "Process", foreign_keys=[to_process_id]
    )
    approved_by_user: Mapped["User"] = relationship(
        "User", back_populates="approved_rollbacks", foreign_keys=[approved_by_id]
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessRollback id={self.id} vehicle={self.vehicle_id} "
            f"from={self.from_process_id} to={self.to_process_id}>"
        )


# ---------------------------------------------------------------------------
# Findings (Damage discovered during repair)
# ---------------------------------------------------------------------------

class Finding(Base):
    """
    An unexpected damage finding discovered during vehicle repair.

    When a finding is reported, the insurance company is immediately
    notified via their dashboard. Three timestamps are recorded:

        reported_at              — When the mechanic logged the finding.
        insurance_acknowledged_at — When the insurer confirmed they saw it
                                   (SLA metric: expected within X hours).
        approved_at              — When the insurer approved the extra budget.

    cost_estimator_ref is a nullable hook for future integration with
    the AI Cost Estimator subproject. When that subproject is ready,
    it will write an estimator result reference here.

    status values:
        'pending'      — Reported; awaiting insurer acknowledgment.
        'acknowledged' — Insurer has seen the finding.
        'approved'     — Extra budget approved; repair can proceed.
        'rejected'     — Extra budget denied.
    """
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    process_log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("process_logs.id"), nullable=False
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    additional_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    photo_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Future hook: reference to AI Cost Estimator result (Phase 7)
    cost_estimator_ref: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    # SLA timestamps
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    insurance_acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="findings")
    process_log: Mapped["ProcessLog"] = relationship(
        "ProcessLog", back_populates="findings"
    )

    def __repr__(self) -> str:
        return (
            f"<Finding id={self.id} vehicle={self.vehicle_id} "
            f"cost={self.additional_cost} status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# Parts & Suppliers
# ---------------------------------------------------------------------------

class Supplier(Base):
    """A supplier of spare parts used in vehicle repairs."""
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parts: Mapped[list["Part"]] = relationship("Part", back_populates="supplier")

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name!r}>"


class Part(Base):
    """
    A spare part available in the workshop inventory.

    stock_quantity is updated whenever a part is used on a vehicle
    (RepairPartUsed). Low-stock alerts can be built on top of this.
    """
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_name: Mapped[str] = mapped_column(String(120), nullable=False)
    part_number: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("suppliers.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier", back_populates="parts"
    )
    used_in: Mapped[list["RepairPartUsed"]] = relationship(
        "RepairPartUsed", back_populates="part"
    )

    def __repr__(self) -> str:
        return f"<Part id={self.id} name={self.part_name!r} stock={self.stock_quantity}>"


class RepairPartUsed(Base):
    """
    Records spare parts consumed during the repair of a specific vehicle.

    total_cost = quantity × part.unit_cost (stored for historical accuracy
    even if unit_cost changes later).
    """
    __tablename__ = "repair_parts_used"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=False
    )
    part_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parts.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_cost_at_time: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="parts_used")
    part: Mapped["Part"] = relationship("Part", back_populates="used_in")

    def __repr__(self) -> str:
        return (
            f"<RepairPartUsed id={self.id} vehicle={self.vehicle_id} "
            f"part={self.part_id} qty={self.quantity}>"
        )


# ---------------------------------------------------------------------------
# Notification Log
# ---------------------------------------------------------------------------

class NotificationLog(Base):
    """
    An audit trail entry for every notification sent to a client.

    NOTE: Notifications are sent to CLIENTS only (WhatsApp/SMS).
    Insurance companies access information via their dashboard —
    they are never contacted via messaging from this system.

    channel values: 'whatsapp' | 'sms' | 'email'
    status values:  'sent' | 'failed' | 'pending'
    """
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vehicles.id"), nullable=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    recipient: Mapped[str] = mapped_column(String(60), nullable=False)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped[Optional["Vehicle"]] = relationship(
        "Vehicle", back_populates="notifications"
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationLog id={self.id} channel={self.channel!r} "
            f"to={self.recipient!r} status={self.status!r}>"
        )
