"""
RES — services/vehicle_service.py
====================================
Business logic for vehicle and customer management.

Provides:
  - Customer creation / lookup by phone number
  - Vehicle registration
  - Checking a vehicle into its first process (Reception)
  - Listing active vehicles for the dashboard
  - Searching vehicles by license plate
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import joinedload

from core.database import get_session
from core.models import Customer, InsuranceCompany, Process, ProcessLog, Vehicle
from core.process_engine import checkin, get_applicable_processes


# ---------------------------------------------------------------------------
# Customer helpers
# ---------------------------------------------------------------------------

def get_or_create_customer(
    full_name: str,
    phone_whatsapp: str,
    email: Optional[str] = None,
    id_document: Optional[str] = None,
) -> Customer:
    """
    Return an existing customer matching phone_whatsapp, or create a new one.

    Args:
        full_name:      Customer's full name.
        phone_whatsapp: WhatsApp-enabled phone number (international format).
        email:          Optional email address.
        id_document:    Optional ID / Passport number.

    Returns:
        The existing or newly created Customer ORM object.
    """
    with get_session() as session:
        existing = session.query(Customer).filter_by(
            phone_whatsapp=phone_whatsapp
        ).first()
        if existing:
            return existing

        customer = Customer(
            full_name=full_name,
            phone_whatsapp=phone_whatsapp,
            email=email,
            id_document=id_document,
        )
        session.add(customer)
        session.flush()
        return customer


def list_insurance_companies() -> list[InsuranceCompany]:
    """
    Return all active insurance companies for use in drop-downs.

    Returns:
        List of InsuranceCompany objects ordered by name.
    """
    with get_session() as session:
        return (
            session.query(InsuranceCompany)
            .filter_by(is_active=True)
            .order_by(InsuranceCompany.name)
            .all()
        )


# ---------------------------------------------------------------------------
# Vehicle registration & reception
# ---------------------------------------------------------------------------

def register_vehicle(
    # Customer
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str] = None,
    customer_id_doc: Optional[str] = None,
    # Vehicle
    license_plate: str = "",
    make: str = "",
    model: str = "",
    year: Optional[int] = None,
    color: Optional[str] = None,
    vin: Optional[str] = None,
    crash_severity: str = "LOW",
    # Insurance
    insurance_company_id: Optional[int] = None,
    claim_number: Optional[str] = None,
    estimated_total_cost: Optional[float] = None,
    notes: Optional[str] = None,
) -> tuple[Vehicle, ProcessLog]:
    """
    Register a new vehicle and immediately check it into Vehicle Reception.

    This is the primary entry point when a vehicle arrives at the workshop.
    It creates (or reuses) the customer record, creates the vehicle record,
    and performs the first process check-in automatically.

    Args:
        customer_name:          Owner's full name.
        customer_phone:         Owner's WhatsApp phone number.
        customer_email:         Optional email.
        customer_id_doc:        Optional ID number.
        license_plate:          Vehicle plate (required).
        make:                   Vehicle make, e.g. "Toyota".
        model:                  Vehicle model, e.g. "Corolla".
        year:                   Vehicle year, e.g. 2019.
        color:                  Vehicle color.
        vin:                    VIN / chassis number.
        crash_severity:         'LOW' or 'HIGH' — drives process routing.
        insurance_company_id:   Optional FK to insurance company.
        claim_number:           Insurance claim reference number.
        estimated_total_cost:   Initial cost estimate (can be updated later).
        notes:                  Intake notes.

    Returns:
        A tuple of (Vehicle, ProcessLog) — the created vehicle and its
        first process check-in log.

    Raises:
        ValueError: If license_plate, make, or model are empty.
        ProcessNotFoundError: If no Reception process is configured.
    """
    if not license_plate.strip():
        raise ValueError("License plate is required.")
    if not make.strip():
        raise ValueError("Vehicle make is required.")
    if not model.strip():
        raise ValueError("Vehicle model is required.")

    with get_session() as session:
        # Get or create customer
        customer = session.query(Customer).filter_by(
            phone_whatsapp=customer_phone
        ).first()
        if not customer:
            customer = Customer(
                full_name=customer_name,
                phone_whatsapp=customer_phone,
                email=customer_email or None,
                id_document=customer_id_doc or None,
            )
            session.add(customer)
            session.flush()

        # Create the vehicle
        vehicle = Vehicle(
            license_plate=license_plate.strip().upper(),
            make=make.strip(),
            model=model.strip(),
            year=year,
            color=color or None,
            vin=vin or None,
            customer_id=customer.id,
            insurance_company_id=insurance_company_id,
            claim_number=claim_number or None,
            crash_severity=crash_severity.upper(),
            reception_date=datetime.utcnow(),
            current_status="reception",
            estimated_total_cost=estimated_total_cost,
            notes=notes or None,
        )
        session.add(vehicle)
        session.flush()   # vehicle.id is now available
        vehicle_id = vehicle.id

    # Check-in to the first applicable process (Vehicle Reception)
    applicable = get_applicable_processes(crash_severity)
    if not applicable:
        raise RuntimeError("No active processes found. Please seed the database.")
    first_process = applicable[0]
    log = checkin(vehicle_id=vehicle_id, process_id=first_process.id)
    return vehicle_id, log


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def get_vehicle_by_plate(plate: str) -> Optional[Vehicle]:
    """
    Search for a vehicle by exact license plate (case-insensitive).

    Args:
        plate: License plate string to search for.

    Returns:
        The Vehicle ORM object, or None if not found.
    """
    with get_session() as session:
        return session.query(Vehicle).filter(
            Vehicle.license_plate.ilike(plate.strip())
        ).filter_by(is_deleted=False).first()


def list_active_vehicles() -> list[Vehicle]:
    """
    Return all non-deleted, non-delivered vehicles.

    Returns:
        List of Vehicle ORM objects with customer and insurance loaded.
    """
    with get_session() as session:
        return (
            session.query(Vehicle)
            .options(
                joinedload(Vehicle.customer),
                joinedload(Vehicle.insurance_company),
            )
            .filter_by(is_deleted=False)
            .filter(Vehicle.current_status.notin_(["delivered"]))
            .order_by(Vehicle.reception_date.desc())
            .all()
        )
