from django.conf import settings
from django.db import models


class Discipline(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CoachProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coach_profile")
    display_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    academy_or_club = models.CharField(max_length=160, blank=True)
    city = models.CharField(max_length=100, blank=True)
    hourly_rate_cents = models.PositiveIntegerField(blank=True, null=True)
    currency = models.CharField(max_length=3, default="EUR")
    cancellation_deadline_hours = models.PositiveIntegerField(default=24)
    accepts_new_students = models.BooleanField(default=True)
    auto_accept_known_students = models.BooleanField(default=False)
    minimum_student_age = models.PositiveSmallIntegerField(blank=True, null=True)
    instagram_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    disciplines = models.ManyToManyField(Discipline, blank=True, related_name="coach_profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    display_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    disciplines = models.ManyToManyField(Discipline, blank=True, related_name="student_profiles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class BlockedStudent(models.Model):
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="blocked_students")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="blocked_by_coaches")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("coach", "student")

    def __str__(self):
        return f"{self.coach} blocked {self.student}"
