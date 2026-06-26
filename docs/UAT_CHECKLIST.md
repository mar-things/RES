# RES UAT Checklist

Run this checklist before production rollout.

## Workshop / Mechanic

- Log in with a mechanic account.
- Register a vehicle.
- Advance a vehicle through the configured route.
- Report a finding with a manual cost and optional photo.
- Confirm dashboard capacity counts and waiting status are visible.

## Manager / Admin

- Log in with a manager or admin account.
- Roll a vehicle back to a prior valid process with a reason.
- Open Reports and export CSV/PDF.
- Run the security audit from Settings.
- Open the kiosk board and confirm no customer PII is displayed.

## Insurance Viewer

- Log in with an insurance-linked account.
- Confirm only that insurer's findings are visible.
- Acknowledge, approve, and reject findings.
- Confirm approved findings no longer appear in the unresolved queue.

## Client Notification

- In development, confirm notification failures are logged without blocking repair flow.
- In production, configure Twilio credentials and verify WhatsApp and SMS delivery.
