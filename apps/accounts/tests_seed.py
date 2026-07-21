from django.core.management import call_command
from django.test import TestCase

from apps.bookings.models import BookingRequest
from apps.notifications.models import Notification
from apps.profiles.models import CoachProfile, StudentProfile
from apps.scheduling.models import AvailabilitySlot


class SeedDevDataTests(TestCase):
    def test_seed_dev_data_is_idempotent(self):
        call_command("seed_dev_data")
        call_command("seed_dev_data")

        self.assertEqual(CoachProfile.objects.count(), 1)
        self.assertEqual(StudentProfile.objects.count(), 1)
        self.assertEqual(AvailabilitySlot.objects.count(), 1)
        self.assertEqual(BookingRequest.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 1)
