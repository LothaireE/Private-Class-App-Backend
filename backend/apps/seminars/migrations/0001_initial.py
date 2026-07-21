from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Seminar",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("location", models.CharField(blank=True, max_length=200)),
                ("capacity", models.PositiveIntegerField(blank=True, null=True)),
                ("external_booking_url", models.URLField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("cancelled", "Cancelled")], default="draft", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seminars", to="profiles.coachprofile")),
                ("discipline", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="seminars", to="profiles.discipline")),
            ],
            options={"ordering": ["starts_at"]},
        ),
    ]
