from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("profiles", "0001_initial"),
        ("scheduling", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookingRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected"), ("cancelled", "Cancelled")], default="pending", max_length=16)),
                ("requested_topic", models.CharField(blank=True, max_length=160)),
                ("message", models.TextField(blank=True)),
                ("rejection_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booking_requests", to="profiles.coachprofile")),
                ("slot", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booking_requests", to="scheduling.availabilityslot")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booking_requests", to="profiles.studentprofile")),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["coach", "status"], name="bookings_bo_coach__92a7ab_idx"),
                    models.Index(fields=["student", "status"], name="bookings_bo_student_2d36ba_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("topic", models.CharField(blank=True, max_length=160)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("status", models.CharField(choices=[("scheduled", "Scheduled"), ("completed", "Completed"), ("cancelled", "Cancelled"), ("no_show", "No show")], default="scheduled", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("booking_request", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="session", to="bookings.bookingrequest")),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="profiles.coachprofile")),
                ("slot", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="session", to="scheduling.availabilityslot")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="profiles.studentprofile")),
            ],
            options={
                "ordering": ["starts_at"],
                "indexes": [
                    models.Index(fields=["coach", "starts_at"], name="bookings_se_coach__d9907a_idx"),
                    models.Index(fields=["student", "starts_at"], name="bookings_se_student_c1de52_idx"),
                    models.Index(fields=["status", "starts_at"], name="bookings_se_status_2d35c8_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Cancellation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cancelled_by", models.CharField(choices=[("coach", "Coach"), ("student", "Student"), ("admin", "Admin")], max_length=16)),
                ("reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cancellations", to="bookings.session")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cancellations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StudentNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_notes", to="bookings.session")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="profiles.studentprofile")),
            ],
            options={"ordering": ["-created_at"], "unique_together": {("session", "student")}},
        ),
    ]
