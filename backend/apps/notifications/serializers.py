from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "kind", "title", "body", "data", "read_at", "created_at"]
        read_only_fields = ["id", "user", "kind", "title", "body", "data", "created_at"]
