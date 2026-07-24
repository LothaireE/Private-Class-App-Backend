from django.db import transaction
from rest_framework import serializers

from apps.profiles.models import BlockedStudent
from apps.scheduling.models import AvailabilitySlot, ProposalWindow

from .models import BookingRequest, Cancellation, Session, StudentNote


class BookingRequestSerializer(serializers.ModelSerializer):
    coach_display_name = serializers.CharField(source="coach.display_name", read_only=True)
    student_display_name = serializers.CharField(source="student.display_name", read_only=True)
    slot_starts_at = serializers.DateTimeField(source="slot.starts_at", read_only=True)
    slot_ends_at = serializers.DateTimeField(source="slot.ends_at", read_only=True)
    slot_topic = serializers.CharField(source="slot.topic", read_only=True)
    slot_location = serializers.CharField(source="slot.location", read_only=True)
    slot_status = serializers.CharField(source="slot.status", read_only=True)
    session_id = serializers.SerializerMethodField()
    session_status = serializers.SerializerMethodField()

    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "slot",
            "coach",
            "student",
            "status",
            "coach_display_name",
            "student_display_name",
            "slot_starts_at",
            "slot_ends_at",
            "slot_topic",
            "slot_location",
            "slot_status",
            "proposal_window",
            "session_id",
            "session_status",
            "requested_topic",
            "message",
            "rejection_reason",
            "cancellation_reason_code",
            "cancellation_note",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "proposal_window",
            "rejection_reason",
            "cancellation_reason_code",
            "cancellation_note",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def get_session_id(self, obj):
        session = getattr(obj, "session", None)
        return session.id if session else None

    def get_session_status(self, obj):
        session = getattr(obj, "session", None)
        return session.status if session else None

    def validate(self, attrs):
        slot = attrs.get("slot") or getattr(self.instance, "slot", None)
        coach = attrs.get("coach") or getattr(self.instance, "coach", None)
        student = attrs.get("student") or getattr(self.instance, "student", None)

        if slot and coach and slot.coach_id != coach.id:
            raise serializers.ValidationError({"coach": "Coach must match the selected slot."})

        allow_pending_proposal = self.context.get("allow_pending_proposal", False)
        valid_new_slot_statuses = [AvailabilitySlot.Status.OPEN]
        if allow_pending_proposal:
            valid_new_slot_statuses.append(AvailabilitySlot.Status.PENDING)
        if not self.instance and slot and slot.status not in valid_new_slot_statuses:
            raise serializers.ValidationError({"slot": "This slot is not open for booking requests."})

        if not self.instance and coach and student:
            if not coach.accepts_new_students:
                raise serializers.ValidationError({"coach": "This coach is not accepting new students."})
            if BlockedStudent.objects.filter(coach=coach, student=student).exists():
                raise serializers.ValidationError("This student cannot request bookings with this coach.")

        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if student and student.user_id != request.user.id:
                raise serializers.ValidationError({"student": "You can only create booking requests for your own student profile."})
            if self.instance and student and self.instance.student.user_id != request.user.id:
                raise serializers.ValidationError("Only the requesting student can update this booking request.")

        if self.instance and self.instance.status != BookingRequest.Status.PENDING:
            raise serializers.ValidationError("Only pending booking requests can be updated.")

        return attrs


class BookingDecisionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class BookingCancelSerializer(serializers.Serializer):
    reason_code = serializers.ChoiceField(choices=BookingRequest.CancellationReason.choices)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["reason_code"] == BookingRequest.CancellationReason.OTHER and not attrs.get("note", "").strip():
            raise serializers.ValidationError({"note": "Please provide a short reason when choosing Other."})
        return attrs


class SessionSerializer(serializers.ModelSerializer):
    coach_display_name = serializers.CharField(source="coach.display_name", read_only=True)
    student_display_name = serializers.CharField(source="student.display_name", read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "booking_request",
            "slot",
            "coach",
            "student",
            "coach_display_name",
            "student_display_name",
            "starts_at",
            "ends_at",
            "topic",
            "location",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CancellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cancellation
        fields = ["id", "session", "cancelled_by", "user", "reason_code", "reason", "created_at"]
        read_only_fields = ["user", "created_at"]


class SessionCancelSerializer(serializers.Serializer):
    reason_code = serializers.ChoiceField(choices=Cancellation.Reason.choices)
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["reason_code"] == Cancellation.Reason.OTHER and not attrs.get("reason", "").strip():
            raise serializers.ValidationError({"reason": "Please provide a short reason when choosing Other."})
        return attrs


class StudentNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentNote
        fields = ["id", "session", "student", "body", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        student = attrs.get("student") or getattr(self.instance, "student", None)
        session = attrs.get("session") or getattr(self.instance, "session", None)

        if request and request.user.is_authenticated:
            if student and student.user_id != request.user.id:
                raise serializers.ValidationError({"student": "You can only manage notes for your own student profile."})
            if session and session.student.user_id != request.user.id:
                raise serializers.ValidationError({"session": "You can only add notes to your own sessions."})

        if self.instance and "student" in attrs and attrs["student"].id != self.instance.student_id:
            raise serializers.ValidationError({"student": "Note owner cannot be changed."})
        if self.instance and "session" in attrs and attrs["session"].id != self.instance.session_id:
            raise serializers.ValidationError({"session": "Note session cannot be changed."})

        return attrs


def accept_booking_request(booking_request):
    with transaction.atomic():
        request = BookingRequest.objects.select_for_update().select_related("slot").get(pk=booking_request.pk)
        slot = AvailabilitySlot.objects.select_for_update().get(pk=request.slot_id)

        if request.status != BookingRequest.Status.PENDING:
            raise serializers.ValidationError("Only pending booking requests can be accepted.")
        if slot.status != AvailabilitySlot.Status.OPEN:
            if slot.status != AvailabilitySlot.Status.PENDING:
                raise serializers.ValidationError("This slot is no longer available.")

        request.status = BookingRequest.Status.ACCEPTED
        request.save(update_fields=["status", "updated_at"])

        slot.status = AvailabilitySlot.Status.RESERVED
        slot.save(update_fields=["status", "updated_at"])

        session = Session.objects.create(
            booking_request=request,
            slot=slot,
            coach=request.coach,
            student=request.student,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            topic=request.requested_topic or slot.topic,
            location=slot.location,
        )

        competing_requests = list(
            BookingRequest.objects.select_for_update()
            .select_related("slot", "student__user")
            .filter(
                coach=request.coach,
                status=BookingRequest.Status.PENDING,
                slot__starts_at__lt=slot.ends_at,
                slot__ends_at__gt=slot.starts_at,
            )
            .exclude(pk=request.pk)
        )
        for competing_request in competing_requests:
            competing_request.status = BookingRequest.Status.REJECTED
            competing_request.rejection_reason = "Another request was accepted for this time."
            competing_request.save(update_fields=["status", "rejection_reason", "updated_at"])
            if competing_request.slot.status == AvailabilitySlot.Status.PENDING:
                competing_request.slot.status = AvailabilitySlot.Status.CANCELLED
                competing_request.slot.save(update_fields=["status", "updated_at"])

        proposal_window = None
        if request.proposal_window_id:
            proposal_window = (
                ProposalWindow.objects.select_for_update()
                .filter(
                    coach=request.coach,
                    active=True,
                    starts_at__lte=slot.starts_at,
                    ends_at__gte=slot.ends_at,
                )
                .first()
            )
        if proposal_window:
            proposal_window.active = False
            proposal_window.save(update_fields=["active", "updated_at"])
            if proposal_window.starts_at < slot.starts_at:
                ProposalWindow.objects.create(
                    coach=request.coach,
                    starts_at=proposal_window.starts_at,
                    ends_at=slot.starts_at,
                    location=proposal_window.location,
                )
            if slot.ends_at < proposal_window.ends_at:
                ProposalWindow.objects.create(
                    coach=request.coach,
                    starts_at=slot.ends_at,
                    ends_at=proposal_window.ends_at,
                    location=proposal_window.location,
                )

        return session, competing_requests
