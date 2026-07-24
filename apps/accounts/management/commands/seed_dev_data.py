from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import BookingRequest
from apps.notifications.services import notify_booking_requested
from apps.profiles.models import CoachProfile, Discipline, StudentProfile
from apps.scheduling.models import AvailabilitySlot, ProposalWindow


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

        coach_two_user, _ = User.objects.get_or_create(
            email="coach2@example.com",
            defaults={
                "username": "coach2",
                "role": User.Role.COACH,
                "first_name": "Maya",
            },
        )
        coach_two_user.set_password("password123")
        coach_two_user.save()

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

        student_two_user, _ = User.objects.get_or_create(
            email="student2@example.com",
            defaults={
                "username": "student2",
                "role": User.Role.STUDENT,
                "first_name": "Nina",
            },
        )
        student_two_user.set_password("password123")
        student_two_user.save()

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
        coach.offered_topics = ["Fundamentals", "Technique review", "Sparring preparation"]
        coach.save(update_fields=["offered_topics", "updated_at"])

        coach_two, _ = CoachProfile.objects.get_or_create(
            user=coach_two_user,
            defaults={
                "display_name": "Maya Coach",
                "bio": "Competition-focused private classes.",
                "city": "Berlin",
                "hourly_rate_cents": 6500,
            },
        )
        coach_two.disciplines.set([jiu_jitsu])
        coach_two.offered_topics = ["Competition strategy", "Guard passing", "Takedowns"]
        coach_two.save(update_fields=["offered_topics", "updated_at"])

        student, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={"display_name": "Sam Student", "city": "Berlin"},
        )
        student.disciplines.set([jiu_jitsu])

        student_two, _ = StudentProfile.objects.get_or_create(
            user=student_two_user,
            defaults={"display_name": "Nina Student", "city": "Berlin"},
        )
        student_two.disciplines.set([jiu_jitsu, music])

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


        coach_two_starts_at = starts_at + timedelta(days=3)
        coach_two_slots = [
            (coach_two_starts_at.replace(hour=10), "Maya morning drills", "North academy", 6500),
            (coach_two_starts_at.replace(hour=17), "Maya sparring prep", "North academy", 7000),
        ]
        for slot_starts_at, topic, location, price_cents in coach_two_slots:
            if not AvailabilitySlot.objects.filter(
                coach=coach_two,
                starts_at__lt=slot_starts_at + timedelta(hours=1),
                ends_at__gt=slot_starts_at,
            ).exclude(status=AvailabilitySlot.Status.CANCELLED).exists():
                AvailabilitySlot.objects.create(
                    coach=coach_two,
                    starts_at=slot_starts_at,
                    ends_at=slot_starts_at + timedelta(hours=1),
                    topic=topic,
                    location=location,
                    discipline=jiu_jitsu,
                    price_cents=price_cents,
                )

        coach_timezone = ZoneInfo(coach.timezone)
        coach_today = timezone.localdate(timezone=coach_timezone)
        days_until_tuesday = (1 - coach_today.weekday()) % 7 or 7
        proposal_date = coach_today + timedelta(days=days_until_tuesday)
        proposal_start = timezone.make_aware(datetime.combine(proposal_date, time(14)), coach_timezone)
        while AvailabilitySlot.objects.filter(
            coach=coach,
            starts_at__lt=proposal_start + timedelta(hours=3),
            ends_at__gt=proposal_start,
        ).exclude(status=AvailabilitySlot.Status.CANCELLED).exists():
            proposal_start += timedelta(days=7)
        ProposalWindow.objects.get_or_create(
            coach=coach,
            starts_at=proposal_start,
            defaults={"ends_at": proposal_start + timedelta(hours=3), "location": "Main academy"},
        )

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("Coach login: coach@example.com / password123")
        self.stdout.write("Coach 2 login: coach2@example.com / password123")
        self.stdout.write("Student login: student@example.com / password123")
        self.stdout.write("Student 2 login: student2@example.com / password123")
