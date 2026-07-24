from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import decorators, exceptions, permissions, response, serializers, status, viewsets
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apps.bookings.models import BookingRequest
from apps.bookings.serializers import BookingRequestSerializer
from apps.notifications.services import notify_booking_requested
from apps.scheduling.models import AvailabilitySlot, ProposalWindow
from apps.scheduling.serializers import AvailabilitySlotSerializer, ProposalWindowSerializer

from .models import BlockedStudent, CoachProfile, Discipline, StudentProfile
from .permissions import IsProfileOwnerOrReadOnly
from .serializers import BlockedStudentSerializer, CoachProfileSerializer, DisciplineSerializer, StudentProfileSerializer


class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [permissions.AllowAny]


class CoachProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CoachProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    def get_queryset(self):
        return CoachProfile.objects.select_related("user").prefetch_related("disciplines")

    def get_permissions(self):
        if self.action in {"schedule", "request_class"}:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        coach = self.get_object()
        requested_date = parse_date(request.query_params.get("date", "")) or timezone.localdate()
        try:
            coach_timezone = ZoneInfo(coach.timezone)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError({"timezone": "The coach timezone is invalid."}) from exc
        day_start = timezone.make_aware(datetime.combine(requested_date, time.min), coach_timezone)
        day_end = day_start + timedelta(days=1)
        slots = AvailabilitySlot.objects.filter(
            coach=coach, starts_at__lt=day_end, ends_at__gt=day_start
        ).exclude(status=AvailabilitySlot.Status.CANCELLED).filter(
            ~Q(status=AvailabilitySlot.Status.PENDING)
            | Q(
                status=AvailabilitySlot.Status.PENDING,
                booking_requests__status="pending",
                booking_requests__coach__user=request.user,
            )
            | Q(
                status=AvailabilitySlot.Status.PENDING,
                booking_requests__status="pending",
                booking_requests__student__user=request.user,
            )
        ).select_related("coach", "discipline").prefetch_related(
            Prefetch(
                "booking_requests",
                queryset=BookingRequest.objects.select_related("coach__user", "student__user", "session"),
                to_attr="schedule_booking_requests",
            )
        ).distinct()
        proposal_windows = ProposalWindow.objects.filter(
            coach=coach, active=True, starts_at__lt=day_end, ends_at__gt=day_start
        ).select_related("coach")
        return response.Response(
            {
                "date": requested_date,
                "timezone": coach.timezone,
                "day_starts_at": coach.day_starts_at.isoformat(),
                "day_ends_at": coach.day_ends_at.isoformat(),
                "break_starts_at": coach.break_starts_at.isoformat() if coach.break_starts_at else None,
                "break_ends_at": coach.break_ends_at.isoformat() if coach.break_ends_at else None,
                "offered_topics": coach.offered_topics,
                "slots": AvailabilitySlotSerializer(slots, many=True, context={"request": request}).data,
                "proposal_windows": ProposalWindowSerializer(proposal_windows, many=True).data,
            }
        )

    @decorators.action(detail=True, methods=["post"], url_path="request-class")
    def request_class(self, request, pk=None):
        coach = self.get_object()
        try:
            student = request.user.student_profile
        except StudentProfile.DoesNotExist as exc:
            raise exceptions.PermissionDenied("A student profile is required to request a class.") from exc

        starts_at = parse_datetime(request.data.get("starts_at", ""))
        ends_at = parse_datetime(request.data.get("ends_at", ""))
        if not starts_at or not ends_at or ends_at <= starts_at:
            raise serializers.ValidationError("Valid starts_at and ends_at values are required.")
        if any(value.minute % 15 or value.second or value.microsecond for value in (starts_at, ends_at)):
            raise serializers.ValidationError("Start and end times must use 15-minute increments.")

        proposal_window = ProposalWindow.objects.filter(
            pk=request.data.get("proposal_window"), coach=coach, active=True
        ).first()
        if not proposal_window:
            raise serializers.ValidationError({"proposal_window": "A valid proposal window is required."})
        if starts_at < proposal_window.starts_at or ends_at > proposal_window.ends_at:
            raise serializers.ValidationError("The requested time must fit inside the selected proposal window.")

        requested_topic = request.data.get("requested_topic", "").strip()
        if requested_topic not in coach.offered_topics:
            raise serializers.ValidationError({"requested_topic": "Choose one of the topics offered by this coach."})

        try:
            coach_timezone = ZoneInfo(coach.timezone)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError({"timezone": "The coach timezone is invalid."}) from exc
        local_start = timezone.localtime(starts_at, coach_timezone)
        local_end = timezone.localtime(ends_at, coach_timezone)
        if local_start.date() != local_end.date():
            raise serializers.ValidationError("A class request must start and end on the same day.")
        if local_start.time() < coach.day_starts_at or local_end.time() > coach.day_ends_at:
            raise serializers.ValidationError("The requested time is outside this coach's working hours.")
        if coach.break_starts_at and coach.break_ends_at:
            overlaps_break = local_start.time() < coach.break_ends_at and local_end.time() > coach.break_starts_at
            if overlaps_break:
                raise serializers.ValidationError("The requested time overlaps this coach's break.")

        try:
            with transaction.atomic():
                locked_window = ProposalWindow.objects.select_for_update().get(pk=proposal_window.pk, active=True)
                if starts_at < locked_window.starts_at or ends_at > locked_window.ends_at:
                    raise serializers.ValidationError("The selected proposal window is no longer available.")
                slot = AvailabilitySlot.objects.create(
                    coach=coach,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    status=AvailabilitySlot.Status.PENDING,
                    topic=requested_topic,
                    location=request.data.get("location", "") or proposal_window.location,
                    price_cents=coach.hourly_rate_cents,
                    currency=coach.currency,
                )
                booking_serializer = BookingRequestSerializer(
                    data={
                        "slot": slot.id,
                        "coach": coach.id,
                        "student": student.id,
                        "requested_topic": requested_topic,
                        "message": request.data.get("message", ""),
                    },
                    context={"request": request, "allow_pending_proposal": True},
                )
                booking_serializer.is_valid(raise_exception=True)
                booking_request = booking_serializer.save(proposal_window=locked_window)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

        notify_booking_requested(booking_request)
        return response.Response(BookingRequestSerializer(booking_request).data, status=status.HTTP_201_CREATED)


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    def get_queryset(self):
        return StudentProfile.objects.select_related("user").prefetch_related("disciplines")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BlockedStudentViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedStudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlockedStudent.objects.select_related("coach", "student").filter(coach__user=self.request.user)

    def perform_create(self, serializer):
        try:
            coach_profile = self.request.user.coach_profile
        except CoachProfile.DoesNotExist as exc:
            raise exceptions.PermissionDenied("Only users with a coach profile can block students.") from exc
        serializer.save(coach=coach_profile)
