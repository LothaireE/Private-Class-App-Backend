from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AvailabilitySlot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("starts_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("status", models.CharField(choices=[("open", "Open"), ("reserved", "Reserved"), ("cancelled", "Cancelled")], default="open", max_length=16)),
                ("capacity", models.PositiveSmallIntegerField(default=1)),
                ("topic", models.CharField(blank=True, max_length=160)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("price_cents", models.PositiveIntegerField(blank=True, null=True)),
                ("currency", models.CharField(default="EUR", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availability_slots", to="profiles.coachprofile")),
                ("discipline", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="availability_slots", to="profiles.discipline")),
            ],
            options={
                "ordering": ["starts_at"],
                "indexes": [
                    models.Index(fields=["coach", "starts_at", "ends_at"], name="scheduling__coach_i_28c29b_idx"),
                    models.Index(fields=["status", "starts_at"], name="scheduling__status_6f25c2_idx"),
                ],
            },
        ),
    ]
