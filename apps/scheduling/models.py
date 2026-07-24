from django.core.exceptions import ValidationError
from django.db import models

from apps.profiles.models import CoachProfile, Discipline


class AvailabilitySlot(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PENDING = "pending", "Pending approval"
        RESERVED = "reserved", "Reserved"
        CANCELLED = "cancelled", "Cancelled"

    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="availability_slots")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    capacity = models.PositiveSmallIntegerField(default=1)
    topic = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=200, blank=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.SET_NULL, blank=True, null=True, related_name="availability_slots")
    price_cents = models.PositiveIntegerField(blank=True, null=True)
    currency = models.CharField(max_length=3, default="EUR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["coach", "starts_at", "ends_at"]),
            models.Index(fields=["status", "starts_at"]),
        ]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("Availability slot must end after it starts.")

        overlapping_slots = AvailabilitySlot.objects.filter(
            coach=self.coach,
            starts_at__lt=self.ends_at,
            ends_at__gt=self.starts_at,
        ).exclude(status__in=[AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED])

        if self.pk:
            overlapping_slots = overlapping_slots.exclude(pk=self.pk)

        if self.status not in [AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED] and overlapping_slots.exists():
            raise ValidationError("Availability slot overlaps another active slot for this coach.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.coach} {self.starts_at:%Y-%m-%d %H:%M}"


class ProposalWindow(models.Model):
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="proposal_windows")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["coach", "starts_at", "ends_at"])]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("A proposal window must end after it starts.")
        overlaps = ProposalWindow.objects.filter(
            coach=self.coach,
            active=True,
            starts_at__lt=self.ends_at,
            ends_at__gt=self.starts_at,
        )
        if self.pk:
            overlaps = overlaps.exclude(pk=self.pk)
        if self.active and overlaps.exists():
            raise ValidationError("Proposal windows cannot overlap.")
        overlapping_slots = AvailabilitySlot.objects.filter(
            coach=self.coach,
            starts_at__lt=self.ends_at,
            ends_at__gt=self.starts_at,
        ).exclude(status__in=[AvailabilitySlot.Status.PENDING, AvailabilitySlot.Status.CANCELLED])
        if self.active and overlapping_slots.exists():
            raise ValidationError("A proposal window cannot overlap an active class.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.coach} proposals {self.starts_at:%Y-%m-%d %H:%M}"
