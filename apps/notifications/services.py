from .models import Notification


def notify_user(user, kind, title, body="", data=None):
    return Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        body=body,
        data=data or {},
    )


def notify_booking_requested(booking_request):
    return notify_user(
        user=booking_request.coach.user,
        kind=Notification.Kind.BOOKING_REQUESTED,
        title="New booking request",
        body=f"{booking_request.student.display_name} requested a class.",
        data={"booking_request_id": booking_request.id},
    )


def notify_booking_accepted(booking_request, session):
    return notify_user(
        user=booking_request.student.user,
        kind=Notification.Kind.BOOKING_ACCEPTED,
        title="Booking accepted",
        body=f"{booking_request.coach.display_name} accepted your class request.",
        data={"booking_request_id": booking_request.id, "session_id": session.id},
    )


def notify_booking_rejected(booking_request):
    return notify_user(
        user=booking_request.student.user,
        kind=Notification.Kind.BOOKING_REJECTED,
        title="Booking rejected",
        body=f"{booking_request.coach.display_name} rejected your class request.",
        data={"booking_request_id": booking_request.id},
    )


def notify_session_cancelled(session, cancelled_by):
    recipient = session.student.user if cancelled_by == "coach" else session.coach.user
    return notify_user(
        user=recipient,
        kind=Notification.Kind.SESSION_CANCELLED,
        title="Session cancelled",
        body="A scheduled class was cancelled.",
        data={"session_id": session.id, "cancelled_by": cancelled_by},
    )
