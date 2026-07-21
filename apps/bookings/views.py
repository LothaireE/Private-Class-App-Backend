from django.db.models import Q
from rest_framework import decorators, exceptions, permissions, response, status, viewsets

from .models import BookingRequest, Cancellation, Session, StudentNote
from .permissions import IsBookingParticipant, IsSessionParticipant, is_coach_owner, is_student_owner
from .serializers import (
    BookingDecisionSerializer,
    BookingRequestSerializer,
    CancellationSerializer,
    SessionCancelSerializer,
    SessionSerializer,
    StudentNoteSerializer,
    accept_booking_request,
)


class BookingRequestViewSet(viewsets.ModelViewSet):
    serializer_class = BookingRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingParticipant]

    def get_queryset(self):
        user = self.request.user
        return BookingRequest.objects.select_related("slot", "coach", "student").filter(
            Q(coach__user=user) | Q(student__user=user)
        )

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @decorators.action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        booking_request = self.get_object()
        if not is_coach_owner(request.user, booking_request.coach):
            raise exceptions.PermissionDenied("Only the coach can accept this booking request.")
        session = accept_booking_request(booking_request)
        return response.Response(SessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        booking_request = self.get_object()
        if not is_coach_owner(request.user, booking_request.coach):
            raise exceptions.PermissionDenied("Only the coach can reject this booking request.")
        if booking_request.status != BookingRequest.Status.PENDING:
            raise exceptions.ValidationError("Only pending booking requests can be rejected.")
        serializer = BookingDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking_request.status = BookingRequest.Status.REJECTED
        booking_request.rejection_reason = serializer.validated_data.get("reason", "")
        booking_request.save(update_fields=["status", "rejection_reason", "updated_at"])
        return response.Response(self.get_serializer(booking_request).data)


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSessionParticipant]

    def get_queryset(self):
        user = self.request.user
        return Session.objects.select_related("booking_request", "slot", "coach", "student").filter(
            Q(coach__user=user) | Q(student__user=user)
        )

    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        session = self.get_object()
        if session.status != Session.Status.SCHEDULED:
            raise exceptions.ValidationError("Only scheduled sessions can be cancelled.")

        if is_coach_owner(request.user, session.coach):
            cancelled_by = Cancellation.CancelledBy.COACH
        elif is_student_owner(request.user, session.student):
            cancelled_by = Cancellation.CancelledBy.STUDENT
        else:
            raise exceptions.PermissionDenied("Only a session participant can cancel it.")

        serializer = SessionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.status = Session.Status.CANCELLED
        session.save(update_fields=["status", "updated_at"])
        cancellation = Cancellation.objects.create(
            session=session,
            cancelled_by=cancelled_by,
            user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return response.Response(CancellationSerializer(cancellation).data, status=status.HTTP_201_CREATED)


class StudentNoteViewSet(viewsets.ModelViewSet):
    serializer_class = StudentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentNote.objects.select_related("session", "student").filter(student__user=self.request.user)
