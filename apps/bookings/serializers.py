from django.db import transaction
from rest_framework import serializers

from apps.profiles.models import BlockedStudent
from apps.scheduling.models import AvailabilitySlot

from .models import BookingRequest, Cancellation, Session, StudentNote


class BookingRequestSerializer(serializers.ModelSerializer):
    coach_display_name = serializers.CharField(source="coach.display_name", read_only=True)
    student_display_name = serializers.CharField(source="student.display_name", read_only=True)
    slot_starts_at = serializers.DateTimeField(source="slot.starts_at", read_only=True)
    slot_ends_at = serializers.DateTimeField(source="slot.ends_at", read_only=True)
    slot_topic = serializers.CharField(source="slot.topic", read_only=True)
    slot_location = serializers.CharField(source="slot.location", read_only=True)
    slot_status = serializers.CharField(source="slot.status", read_only=True)

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
            "requested_topic",
            "message",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "rejection_reason", "created_at", "updated_at"]

    def validate(self, attrs):
        slot = attrs.get("slot") or getattr(self.instance, "slot", None)
        coach = attrs.get("coach") or getattr(self.instance, "coach", None)
        student = attrs.get("student") or getattr(self.instance, "student", None)

        if slot and coach and slot.coach_id != coach.id:
            raise serializers.ValidationError({"coach": "Coach must match the selected slot."})

        if not self.instance and slot and slot.status != AvailabilitySlot.Status.OPEN:
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


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = [
            "id",
            "booking_request",
            "slot",
            "coach",
            "student",
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
        fields = ["id", "session", "cancelled_by", "user", "reason", "created_at"]
        read_only_fields = ["user", "created_at"]


class SessionCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


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
            raise serializers.ValidationError("This slot is no longer open.")

        request.status = BookingRequest.Status.ACCEPTED
        request.save(update_fields=["status", "updated_at"])

        slot.status = AvailabilitySlot.Status.RESERVED
        slot.save(update_fields=["status", "updated_at"])

        return Session.objects.create(
            booking_request=request,
            slot=slot,
            coach=request.coach,
            student=request.student,
            starts_at=slot.starts_at,
            ends_at=slot.ends_at,
            topic=request.requested_topic or slot.topic,
            location=slot.location,
        )
