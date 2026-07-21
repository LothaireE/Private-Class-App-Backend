from rest_framework import serializers

from .models import User


class AccountMeSerializer(serializers.ModelSerializer):
    coach_profile_id = serializers.IntegerField(source="coach_profile.id", read_only=True)
    student_profile_id = serializers.IntegerField(source="student_profile.id", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "phone",
            "coach_profile_id",
            "student_profile_id",
        ]
        read_only_fields = fields
