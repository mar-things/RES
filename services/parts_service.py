"""
RES - services/parts_service.py
================================
Inventory and vehicle parts cost management.

The service owns supplier creation, part stock updates, and recording parts
used against vehicles so cost reports can include material spend.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.database import get_session
from core.models import Part, RepairPartUsed, Supplier, Vehicle


@dataclass(frozen=True)
class VehiclePartsCost:
    """Parts-only cost summary for one vehicle."""

    vehicle_id: int
    plate: str
    total_parts_cost: float
    line_count: int


def create_supplier(
    name: str,
    contact_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> Supplier:
    """
    Create a supplier record.

    Args:
        name: Supplier display name.
        contact_name: Optional contact person.
        phone: Optional phone number.
        email: Optional email address.

    Returns:
        The persisted Supplier.
    """
    if not name.strip():
        raise ValueError("Supplier name is required.")
    with get_session() as session:
        supplier = Supplier(
            name=name.strip(),
            contact_name=contact_name or None,
            phone=phone or None,
            email=email or None,
            is_active=True,
        )
        session.add(supplier)
        session.flush()
        return supplier


def create_part(
    part_name: str,
    part_number: str | None = None,
    unit_cost: float = 0.0,
    stock_quantity: int = 0,
    supplier_id: int | None = None,
) -> Part:
    """
    Create an inventory part.

    Args:
        part_name: Part display name.
        part_number: Optional supplier/manufacturer number.
        unit_cost: Current unit cost.
        stock_quantity: Quantity currently on hand.
        supplier_id: Optional Supplier foreign key.

    Returns:
        The persisted Part.
    """
    if not part_name.strip():
        raise ValueError("Part name is required.")
    if unit_cost < 0:
        raise ValueError("Unit cost cannot be negative.")
    if stock_quantity < 0:
        raise ValueError("Stock quantity cannot be negative.")

    with get_session() as session:
        if supplier_id and not session.get(Supplier, supplier_id):
            raise ValueError(f"Supplier {supplier_id} does not exist.")
        part = Part(
            part_name=part_name.strip(),
            part_number=part_number or None,
            unit_cost=unit_cost,
            stock_quantity=stock_quantity,
            supplier_id=supplier_id,
            is_active=True,
        )
        session.add(part)
        session.flush()
        return part


def list_parts(include_inactive: bool = False) -> list[Part]:
    """
    Return inventory parts ordered by name.

    Args:
        include_inactive: Include inactive parts when True.

    Returns:
        List of Part objects.
    """
    with get_session() as session:
        query = session.query(Part)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(Part.part_name).all()


def record_part_used(vehicle_id: int, part_id: int, quantity: int = 1) -> RepairPartUsed:
    """
    Record inventory consumed by a vehicle repair.

    Args:
        vehicle_id: Vehicle primary key.
        part_id: Part primary key.
        quantity: Quantity consumed.

    Returns:
        The persisted RepairPartUsed record.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    with get_session() as session:
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle or vehicle.is_deleted:
            raise ValueError(f"Vehicle {vehicle_id} does not exist or is deleted.")

        part = session.get(Part, part_id)
        if not part or not part.is_active:
            raise ValueError(f"Part {part_id} does not exist or is inactive.")
        if part.stock_quantity < quantity:
            raise ValueError(
                f"Insufficient stock for '{part.part_name}': "
                f"{part.stock_quantity} available, {quantity} requested."
            )

        part.stock_quantity -= quantity
        total_cost = quantity * part.unit_cost
        used = RepairPartUsed(
            vehicle_id=vehicle_id,
            part_id=part_id,
            quantity=quantity,
            unit_cost_at_time=part.unit_cost,
            total_cost=total_cost,
        )
        session.add(used)
        session.flush()
        return used


def vehicle_parts_cost(vehicle_id: int) -> VehiclePartsCost:
    """
    Summarize parts used by one vehicle.

    Args:
        vehicle_id: Vehicle primary key.

    Returns:
        VehiclePartsCost summary.
    """
    with get_session() as session:
        vehicle = session.get(Vehicle, vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} does not exist.")
        lines = session.query(RepairPartUsed).filter_by(vehicle_id=vehicle_id).all()
        return VehiclePartsCost(
            vehicle_id=vehicle_id,
            plate=vehicle.license_plate,
            total_parts_cost=sum(line.total_cost for line in lines),
            line_count=len(lines),
        )
