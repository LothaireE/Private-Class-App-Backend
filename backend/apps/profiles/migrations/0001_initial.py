from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Discipline",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CoachProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=120)),
                ("bio", models.TextField(blank=True)),
                ("academy_or_club", models.CharField(blank=True, max_length=160)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("hourly_rate_cents", models.PositiveIntegerField(blank=True, null=True)),
                ("currency", models.CharField(default="EUR", max_length=3)),
                ("cancellation_deadline_hours", models.PositiveIntegerField(default=24)),
                ("accepts_new_students", models.BooleanField(default=True)),
                ("auto_accept_known_students", models.BooleanField(default=False)),
                ("minimum_student_age", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("instagram_url", models.URLField(blank=True)),
                ("whatsapp_url", models.URLField(blank=True)),
                ("website_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("disciplines", models.ManyToManyField(blank=True, related_name="coach_profiles", to="profiles.discipline")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="coach_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_name"]},
        ),
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=120)),
                ("bio", models.TextField(blank=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("birth_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("disciplines", models.ManyToManyField(blank=True, related_name="student_profiles", to="profiles.discipline")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="student_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["display_name"]},
        ),
        migrations.CreateModel(
            name="BlockedStudent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="blocked_students", to="profiles.coachprofile")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="blocked_by_coaches", to="profiles.studentprofile")),
            ],
            options={"unique_together": {("coach", "student")}},
        ),
    ]
