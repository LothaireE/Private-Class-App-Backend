from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profiles.models import CoachProfile
from apps.scheduling.models import AvailabilitySlot


class AvailabilitySlotOverlapTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.coach_user = User.objects.create_user(
            username="coach",
            email="coach@example.com",
            password="password",
            role=User.Role.COACH,
        )
        self.coach = CoachProfile.objects.create(user=self.coach_user, display_name="Coach")
        self.starts_at = timezone.now() + timedelta(days=1)
        self.ends_at = self.starts_at + timedelta(hours=1)
        self.slot = AvailabilitySlot.objects.create(
            coach=self.coach,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
        )

    def test_model_rejects_overlapping_active_slots(self):
        slot = AvailabilitySlot(
            coach=self.coach,
            starts_at=self.starts_at + timedelta(minutes=30),
            ends_at=self.ends_at + timedelta(minutes=30),
        )

        with self.assertRaises(ValidationError):
            slot.full_clean()

    def test_api_rejects_overlapping_active_slots(self):
        self.client.force_authenticate(user=self.coach_user)

        response = self.client.post(
            reverse("availability-slot-list"),
            {
                "coach": self.coach.id,
                "starts_at": (self.starts_at + timedelta(minutes=15)).isoformat(),
                "ends_at": (self.ends_at + timedelta(minutes=15)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjacent_slots_are_allowed(self):
        self.client.force_authenticate(user=self.coach_user)

        response = self.client.post(
            reverse("availability-slot-list"),
            {
                "coach": self.coach.id,
                "starts_at": self.ends_at.isoformat(),
                "ends_at": (self.ends_at + timedelta(hours=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
