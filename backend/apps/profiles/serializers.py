from rest_framework import serializers

from .models import BlockedStudent, CoachProfile, Discipline, StudentProfile


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ["id", "name", "slug"]


class CoachProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachProfile
        fields = [
            "id",
            "user",
            "display_name",
            "bio",
            "academy_or_club",
            "city",
            "hourly_rate_cents",
            "currency",
            "cancellation_deadline_hours",
            "accepts_new_students",
            "auto_accept_known_students",
            "minimum_student_age",
            "instagram_url",
            "whatsapp_url",
            "website_url",
            "disciplines",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["id", "user", "display_name", "bio", "city", "birth_date", "disciplines", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class BlockedStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedStudent
        fields = ["id", "coach", "student", "reason", "created_at"]
        read_only_fields = ["coach", "created_at"]
