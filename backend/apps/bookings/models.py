from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.profiles.models import CoachProfile, StudentProfile
from apps.scheduling.models import AvailabilitySlot


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.CASCADE, related_name="booking_requests")
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="booking_requests")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="booking_requests")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    requested_topic = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["coach", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def clean(self):
        if self.slot_id and self.coach_id and self.slot.coach_id != self.coach_id:
            raise ValidationError("Booking request coach must match the slot coach.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} -> {self.coach} ({self.status})"


class Session(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No show"

    booking_request = models.OneToOneField(BookingRequest, on_delete=models.PROTECT, related_name="session")
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.PROTECT, related_name="session")
    coach = models.ForeignKey(CoachProfile, on_delete=models.PROTECT, related_name="sessions")
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name="sessions")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    topic = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["coach", "starts_at"]),
            models.Index(fields=["student", "starts_at"]),
            models.Index(fields=["status", "starts_at"]),
        ]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("Session must end after it starts.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.coach} with {self.student} at {self.starts_at:%Y-%m-%d %H:%M}"


class Cancellation(models.Model):
    class CancelledBy(models.TextChoices):
        COACH = "coach", "Coach"
        STUDENT = "student", "Student"
        ADMIN = "admin", "Admin"

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="cancellations")
    cancelled_by = models.CharField(max_length=16, choices=CancelledBy.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="cancellations")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session} cancelled by {self.cancelled_by}"


class StudentNote(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="student_notes")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="notes")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("session", "student")

    def __str__(self):
        return f"Note by {self.student} for {self.session}"
