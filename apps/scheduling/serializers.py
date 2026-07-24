from rest_framework import serializers

from .models import AvailabilitySlot, ProposalWindow


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    coach_display_name = serializers.CharField(source="coach.display_name", read_only=True)
    viewer_booking_request_id = serializers.SerializerMethodField()
    viewer_booking_request_status = serializers.SerializerMethodField()
    viewer_session_id = serializers.SerializerMethodField()
    viewer_can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilitySlot
        fields = [
            "id",
            "coach",
            "coach_display_name",
            "starts_at",
            "ends_at",
            "status",
            "capacity",
            "topic",
            "location",
            "discipline",
            "price_cents",
            "currency",
            "viewer_booking_request_id",
            "viewer_booking_request_status",
            "viewer_session_id",
            "viewer_can_cancel",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]

    def validate_coach(self, coach):
        request = self.context.get("request")
        if request and request.user.is_authenticated and coach.user_id != request.user.id:
            raise serializers.ValidationError("You can only manage availability slots for your own coach profile.")
        return coach

    def validate(self, attrs):
        if self.instance and "coach" in attrs and attrs["coach"].id != self.instance.coach_id:
            raise serializers.ValidationError({"coach": "Slot coach cannot be changed."})

        coach = attrs.get("coach") or getattr(self.instance, "coach", None)
        starts_at = attrs.get("starts_at") or getattr(self.instance, "starts_at", None)
        ends_at = attrs.get("ends_at") or getattr(self.instance, "ends_at", None)

        if coach and starts_at and ends_at:
            overlapping_slots = AvailabilitySlot.objects.filter(
                coach=coach,
                starts_at__lt=ends_at,
                ends_at__gt=starts_at,
            ).exclude(status__in=[AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED])

            if self.instance:
                overlapping_slots = overlapping_slots.exclude(pk=self.instance.pk)

            next_status = attrs.get("status", getattr(self.instance, "status", AvailabilitySlot.Status.OPEN))
            if next_status not in [AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED] and overlapping_slots.exists():
                raise serializers.ValidationError("Availability slot overlaps another active slot for this coach.")

        return attrs

    def _viewer_booking(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        bookings = getattr(obj, "schedule_booking_requests", None)
        if bookings is None:
            bookings = obj.booking_requests.select_related("coach__user", "student__user", "session").all()
        participant_bookings = [
            booking
            for booking in bookings
            if booking.coach.user_id == request.user.id or booking.student.user_id == request.user.id
        ]
        status_priority = {"accepted": 0, "pending": 1, "rejected": 2, "cancelled": 3}
        return min(participant_bookings, key=lambda booking: status_priority[booking.status], default=None)

    def get_viewer_booking_request_id(self, obj):
        booking = self._viewer_booking(obj)
        return booking.id if booking else None

    def get_viewer_booking_request_status(self, obj):
        booking = self._viewer_booking(obj)
        return booking.status if booking else None

    def get_viewer_session_id(self, obj):
        booking = self._viewer_booking(obj)
        session = getattr(booking, "session", None) if booking else None
        return session.id if session else None

    def get_viewer_can_cancel(self, obj):
        booking = self._viewer_booking(obj)
        if not booking:
            return False
        request = self.context["request"]
        if booking.status == booking.Status.PENDING:
            return booking.student.user_id == request.user.id
        session = getattr(booking, "session", None)
        return bool(session and session.status == session.Status.SCHEDULED)


class ProposalWindowSerializer(serializers.ModelSerializer):
    coach_display_name = serializers.CharField(source="coach.display_name", read_only=True)

    class Meta:
        model = ProposalWindow
        fields = ["id", "coach", "coach_display_name", "starts_at", "ends_at", "location", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_coach(self, coach):
        request = self.context.get("request")
        if request and request.user.is_authenticated and coach.user_id != request.user.id:
            raise serializers.ValidationError("You can only manage your own proposal windows.")
        return coach

    def validate(self, attrs):
        coach = attrs.get("coach") or getattr(self.instance, "coach", None)
        starts_at = attrs.get("starts_at") or getattr(self.instance, "starts_at", None)
        ends_at = attrs.get("ends_at") or getattr(self.instance, "ends_at", None)
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError("A proposal window must end after it starts.")
        if coach and starts_at and ends_at:
            overlaps = ProposalWindow.objects.filter(
                coach=coach, active=True, starts_at__lt=ends_at, ends_at__gt=starts_at
            )
            if self.instance:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if attrs.get("active", getattr(self.instance, "active", True)) and overlaps.exists():
                raise serializers.ValidationError("Proposal windows cannot overlap.")
            overlapping_slots = AvailabilitySlot.objects.filter(
                coach=coach, starts_at__lt=ends_at, ends_at__gt=starts_at
            ).exclude(status__in=[AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED])
            if attrs.get("active", getattr(self.instance, "active", True)) and overlapping_slots.exists():
                raise serializers.ValidationError("A proposal window cannot overlap an active class.")
        return attrs
