"""
RES — services/notification_service.py
=========================================
Client notification dispatcher.

IMPORTANT: Notifications are sent to CLIENTS only (WhatsApp / SMS).
Insurance companies access information via the Insurance Dashboard —
they are NEVER contacted through this notification service.

The dispatcher selects the appropriate provider based on AppConfig:
  - Development / MVP: pywhatkit (WhatsApp Web automation)
  - Production:        Twilio WhatsApp Business API + Twilio SMS

All notifications are logged to the notification_log table for audit.
"""

from datetime import datetime
from typing import Optional

from config import AppConfig
from core.database import get_session
from core.models import NotificationLog


# ---------------------------------------------------------------------------
# Message templates (all strings go through tr() in the UI layer;
# these service-layer messages use English as the base language)
# ---------------------------------------------------------------------------

def _checkin_message(plate: str, process_name: str) -> str:
    return f"Your vehicle ({plate}) has entered the {process_name} stage."


def _checkout_message(plate: str, process_name: str) -> str:
    return f"Your vehicle ({plate}) has completed the {process_name} stage."


def _finding_message(plate: str) -> str:
    return (
        f"Additional damage was found on your vehicle ({plate}) during repair. "
        "We are awaiting insurance approval to proceed. We will keep you updated."
    )


def _ready_message(plate: str) -> str:
    return (
        f"Great news! Your vehicle ({plate}) has passed Quality Assurance "
        "and is ready for pickup. Please contact us to schedule collection."
    )


# ---------------------------------------------------------------------------
# Internal logging
# ---------------------------------------------------------------------------

def _log_notification(
    vehicle_id: Optional[int],
    channel: str,
    recipient: str,
    body: str,
    status: str,
    error: Optional[str] = None,
) -> None:
    """
    Persist a notification record to the notification_log table.

    Args:
        vehicle_id: The vehicle the notification relates to (optional).
        channel:    'whatsapp' | 'sms' | 'email'
        recipient:  Phone number or email address.
        body:       The full message text sent.
        status:     'sent' | 'failed'
        error:      Error detail if status is 'failed'.
    """
    with get_session() as session:
        session.add(NotificationLog(
            vehicle_id=vehicle_id,
            channel=channel,
            recipient=recipient,
            message_body=body,
            sent_at=datetime.utcnow(),
            status=status,
            error_detail=error,
        ))


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

def _send_whatsapp(phone: str, message: str) -> bool:
    """
    Send a WhatsApp message using the configured provider.

    In development mode, uses pywhatkit (requires WhatsApp Web open).
    In production mode, uses Twilio WhatsApp Business API.

    Args:
        phone:   Recipient phone number in international format (+XXXXXXXXXXX).
        message: Message text to send.

    Returns:
        True if sent successfully, False if an error occurred.
    """
    if AppConfig.USE_TWILIO:
        return _send_via_twilio_whatsapp(phone, message)
    else:
        return _send_via_pywhatkit(phone, message)


def _send_via_pywhatkit(phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via pywhatkit (MVP / development only).

    NOTE: pywhatkit requires WhatsApp Web to be open and logged in
    on the running PC. It is NOT suitable for production use.

    Args:
        phone:   Recipient phone (international format).
        message: Message text.

    Returns:
        True on success, False on failure.
    """
    try:
        import pywhatkit as kit
        # wait_time=20s, tab_close=True, close_time=3s
        kit.sendwhatmsg_instantly(phone, message, 20, True, 3)
        return True
    except Exception as exc:
        print(f"[Notification] pywhatkit error: {exc}")
        return False


def _send_via_twilio_whatsapp(phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio's WhatsApp Business API.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and
    TWILIO_WHATSAPP_FROM to be set in .env.

    Args:
        phone:   Recipient phone (international format).
        message: Message text.

    Returns:
        True on success, False on failure.
    """
    try:
        from twilio.rest import Client
        client = Client(AppConfig.TWILIO_ACCOUNT_SID, AppConfig.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=AppConfig.TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{phone}",
        )
        return True
    except Exception as exc:
        print(f"[Notification] Twilio WhatsApp error: {exc}")
        return False


# ---------------------------------------------------------------------------
# Public event dispatchers
# ---------------------------------------------------------------------------

def notify_checkin(
    vehicle_id: int,
    plate: str,
    process_name: str,
    customer_phone: str,
) -> None:
    """
    Send a check-in notification to the client when their vehicle
    enters a repair process.

    Args:
        vehicle_id:     Vehicle primary key (for logging).
        plate:          Vehicle license plate (shown in message).
        process_name:   Name of the process the vehicle entered.
        customer_phone: Client's WhatsApp-enabled phone number.
    """
    body = _checkin_message(plate, process_name)
    success = _send_whatsapp(customer_phone, body)
    _log_notification(
        vehicle_id=vehicle_id,
        channel="whatsapp",
        recipient=customer_phone,
        body=body,
        status="sent" if success else "failed",
    )


def notify_checkout(
    vehicle_id: int,
    plate: str,
    process_name: str,
    customer_phone: str,
) -> None:
    """
    Send a check-out notification to the client when their vehicle
    completes a repair process.

    Args:
        vehicle_id:     Vehicle primary key (for logging).
        plate:          Vehicle license plate.
        process_name:   Name of the completed process.
        customer_phone: Client's WhatsApp-enabled phone number.
    """
    body = _checkout_message(plate, process_name)
    success = _send_whatsapp(customer_phone, body)
    _log_notification(
        vehicle_id=vehicle_id,
        channel="whatsapp",
        recipient=customer_phone,
        body=body,
        status="sent" if success else "failed",
    )


def notify_finding(vehicle_id: int, plate: str, customer_phone: str) -> None:
    """
    Notify the client that additional damage was found during repair.

    Args:
        vehicle_id:     Vehicle primary key.
        plate:          Vehicle license plate.
        customer_phone: Client's WhatsApp-enabled phone number.
    """
    body = _finding_message(plate)
    success = _send_whatsapp(customer_phone, body)
    _log_notification(
        vehicle_id=vehicle_id,
        channel="whatsapp",
        recipient=customer_phone,
        body=body,
        status="sent" if success else "failed",
    )


def notify_ready_for_pickup(
    vehicle_id: int, plate: str, customer_phone: str
) -> None:
    """
    Send the final 'Vehicle Ready for Pickup' notification to the client
    after the vehicle passes Quality Assurance.

    Args:
        vehicle_id:     Vehicle primary key.
        plate:          Vehicle license plate.
        customer_phone: Client's WhatsApp-enabled phone number.
    """
    body = _ready_message(plate)
    success = _send_whatsapp(customer_phone, body)
    _log_notification(
        vehicle_id=vehicle_id,
        channel="whatsapp",
        recipient=customer_phone,
        body=body,
        status="sent" if success else "failed",
    )
