from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import BookingRequest
from apps.notifications.services import notify_booking_requested
from apps.profiles.models import CoachProfile, Discipline, StudentProfile
from apps.scheduling.models import AvailabilitySlot


class Command(BaseCommand):
    help = "Create deterministic development data for the Private Class App backend."

    def handle(self, *args, **options):
        User = get_user_model()
        jiu_jitsu, _ = Discipline.objects.get_or_create(name="Jiu Jitsu", slug="jiu-jitsu")
        music, _ = Discipline.objects.get_or_create(name="Guitar", slug="guitar")

        coach_user, _ = User.objects.get_or_create(
            email="coach@example.com",
            defaults={
                "username": "coach",
                "role": User.Role.COACH,
                "first_name": "Alex",
            },
        )
        coach_user.set_password("password123")
        coach_user.save()

        student_user, _ = User.objects.get_or_create(
            email="student@example.com",
            defaults={
                "username": "student",
                "role": User.Role.STUDENT,
                "first_name": "Sam",
            },
        )
        student_user.set_password("password123")
        student_user.save()

        coach, _ = CoachProfile.objects.get_or_create(
            user=coach_user,
            defaults={
                "display_name": "Alex Coach",
                "bio": "Private classes and seminars.",
                "city": "Berlin",
                "hourly_rate_cents": 5000,
            },
        )
        coach.disciplines.set([jiu_jitsu, music])

        student, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={"display_name": "Sam Student", "city": "Berlin"},
        )
        student.disciplines.set([jiu_jitsu])

        starts_at = (timezone.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        slot, _ = AvailabilitySlot.objects.get_or_create(
            coach=coach,
            starts_at=starts_at,
            defaults={
                "ends_at": starts_at + timedelta(hours=1),
                "topic": "Intro private class",
                "location": "Main academy",
                "discipline": jiu_jitsu,
                "price_cents": 5000,
            },
        )

        booking, created = BookingRequest.objects.get_or_create(
            slot=slot,
            coach=coach,
            student=student,
            defaults={"requested_topic": "Fundamentals"},
        )
        if created:
            notify_booking_requested(booking)

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("Coach login: coach@example.com / password123")
        self.stdout.write("Student login: student@example.com / password123")
