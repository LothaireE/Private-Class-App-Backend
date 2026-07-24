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
            "timezone",
            "day_starts_at",
            "day_ends_at",
            "break_starts_at",
            "break_ends_at",
            "instagram_url",
            "whatsapp_url",
            "website_url",
            "disciplines",
            "offered_topics",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance
        day_starts_at = attrs.get("day_starts_at", getattr(instance, "day_starts_at", None))
        day_ends_at = attrs.get("day_ends_at", getattr(instance, "day_ends_at", None))
        break_starts_at = attrs.get("break_starts_at", getattr(instance, "break_starts_at", None))
        break_ends_at = attrs.get("break_ends_at", getattr(instance, "break_ends_at", None))

        if day_starts_at and day_ends_at and day_ends_at <= day_starts_at:
            raise serializers.ValidationError({"day_ends_at": "The working day must end after it starts."})
        if bool(break_starts_at) != bool(break_ends_at):
            raise serializers.ValidationError("Both break times must be provided together.")
        if break_starts_at and break_ends_at:
            if break_ends_at <= break_starts_at:
                raise serializers.ValidationError({"break_ends_at": "The break must end after it starts."})
            if day_starts_at and day_ends_at and not (day_starts_at <= break_starts_at < break_ends_at <= day_ends_at):
                raise serializers.ValidationError("The break must be inside the working day.")

        return attrs

    def validate_offered_topics(self, topics):
        if not isinstance(topics, list) or any(not isinstance(topic, str) or not topic.strip() for topic in topics):
            raise serializers.ValidationError("Offered topics must be a list of non-empty strings.")
        return list(dict.fromkeys(topic.strip() for topic in topics))


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
