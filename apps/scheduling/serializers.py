from rest_framework import serializers

from .models import AvailabilitySlot


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = [
            "id",
            "coach",
            "starts_at",
            "ends_at",
            "status",
            "capacity",
            "topic",
            "location",
            "discipline",
            "price_cents",
            "currency",
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
        return attrs
