from django.db import models

from apps.profiles.models import CoachProfile, Discipline


class Seminar(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="seminars")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)
    external_booking_url = models.URLField(blank=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.SET_NULL, blank=True, null=True, related_name="seminars")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title
