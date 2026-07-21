from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        BOOKING_REQUESTED = "booking_requested", "Booking requested"
        BOOKING_ACCEPTED = "booking_accepted", "Booking accepted"
        BOOKING_REJECTED = "booking_rejected", "Booking rejected"
        SESSION_CANCELLED = "session_cancelled", "Session cancelled"
        SLOT_OPENED = "slot_opened", "Slot opened"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "read_at"]),
            models.Index(fields=["kind", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"
