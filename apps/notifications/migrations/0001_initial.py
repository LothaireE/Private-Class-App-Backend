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
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("booking_requested", "Booking requested"), ("booking_accepted", "Booking accepted"), ("booking_rejected", "Booking rejected"), ("session_cancelled", "Session cancelled"), ("slot_opened", "Slot opened")], max_length=32)),
                ("title", models.CharField(max_length=160)),
                ("body", models.TextField(blank=True)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["user", "read_at"], name="notificatio_user_id_1f8309_idx"),
                    models.Index(fields=["kind", "created_at"], name="notificatio_kind_8b5c59_idx"),
                ],
            },
        ),
    ]
