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
        demo_slot, _ = AvailabilitySlot.objects.get_or_create(
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
            slot=demo_slot,
            coach=coach,
            student=student,
            defaults={"requested_topic": "Fundamentals"},
        )
        if created:
            notify_booking_requested(booking)

        open_slot = (
            AvailabilitySlot.objects.filter(coach=coach, status=AvailabilitySlot.Status.OPEN)
            .exclude(booking_requests__isnull=False)
            .first()
        )
        if open_slot is None:
            open_starts_at = starts_at + timedelta(days=1)
            while AvailabilitySlot.objects.filter(
                coach=coach,
                starts_at__lt=open_starts_at + timedelta(hours=1),
                ends_at__gt=open_starts_at,
            ).exclude(status=AvailabilitySlot.Status.CANCELLED).exists():
                open_starts_at += timedelta(days=1)

            AvailabilitySlot.objects.create(
                coach=coach,
                starts_at=open_starts_at,
                ends_at=open_starts_at + timedelta(hours=1),
                topic="Open booking slot",
                location="Main academy",
                discipline=jiu_jitsu,
                price_cents=5000,
            )

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("Coach login: coach@example.com / password123")
        self.stdout.write("Student login: student@example.com / password123")
