from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from zoneinfo import ZoneInfo

from apps.bookings.models import BookingRequest
from apps.profiles.models import CoachProfile, StudentProfile
from apps.scheduling.models import AvailabilitySlot, ProposalWindow


class CoachCalendarApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.coach_user = User.objects.create_user(
            username="calendar-coach", email="calendar-coach@example.com", password="password", role=User.Role.COACH
        )
        self.student_user = User.objects.create_user(
            username="calendar-student", email="calendar-student@example.com", password="password", role=User.Role.STUDENT
        )
        self.other_student_user = User.objects.create_user(
            username="other-calendar-student",
            email="other-calendar-student@example.com",
            password="password",
            role=User.Role.STUDENT,
        )
        self.other_coach_user = User.objects.create_user(
            username="other-calendar-coach",
            email="other-calendar-coach@example.com",
            password="password",
            role=User.Role.COACH,
        )
        self.coach = CoachProfile.objects.create(
            user=self.coach_user,
            display_name="Calendar Coach",
            day_starts_at=time(8),
            day_ends_at=time(20),
            break_starts_at=time(12),
            break_ends_at=time(13),
            offered_topics=["Fundamentals", "Technique review"],
        )
        self.student = StudentProfile.objects.create(user=self.student_user, display_name="Calendar Student")
        self.other_student = StudentProfile.objects.create(user=self.other_student_user, display_name="Other Student")
        CoachProfile.objects.create(user=self.other_coach_user, display_name="Other Coach")
        self.day = timezone.localdate() + timedelta(days=2)
        self.proposal_window = ProposalWindow.objects.create(
            coach=self.coach,
            starts_at=self.aware_at(14),
            ends_at=self.aware_at(17),
            location="Main academy",
        )

    def aware_at(self, hour, minute=0):
        return timezone.make_aware(datetime.combine(self.day, time(hour, minute)), ZoneInfo(self.coach.timezone))

    def test_schedule_exposes_working_hours_and_slots(self):
        slot = AvailabilitySlot.objects.create(
            coach=self.coach,
            starts_at=self.aware_at(10),
            ends_at=self.aware_at(11),
            topic="Technique",
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("coach-profile-schedule", args=[self.coach.id]), {"date": self.day.isoformat()})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["day_starts_at"], "08:00:00")
        self.assertEqual(response.data["slots"][0]["id"], slot.id)
        self.assertEqual(response.data["proposal_windows"][0]["id"], self.proposal_window.id)

    def test_student_can_request_a_vacant_time(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("coach-profile-request-class", args=[self.coach.id]),
            {
                "proposal_window": self.proposal_window.id,
                "starts_at": self.aware_at(14, 15).isoformat(),
                "ends_at": self.aware_at(15, 45).isoformat(),
                "requested_topic": "Fundamentals",
                "message": "Are you available?",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = BookingRequest.objects.get(pk=response.data["id"])
        self.assertEqual(booking.status, BookingRequest.Status.PENDING)
        self.assertEqual(booking.slot.status, AvailabilitySlot.Status.PENDING)
        self.assertEqual(booking.proposal_window, self.proposal_window)
        self.assertEqual(booking.slot.coach, self.coach)
        self.proposal_window.refresh_from_db()
        self.assertTrue(self.proposal_window.active)

    def test_pending_request_is_private_but_window_remains_available(self):
        self.client.force_authenticate(user=self.student_user)
        create_response = self.client.post(
            reverse("coach-profile-request-class", args=[self.coach.id]),
            {
                "proposal_window": self.proposal_window.id,
                "starts_at": self.aware_at(14, 15).isoformat(),
                "ends_at": self.aware_at(15, 45).isoformat(),
                "requested_topic": "Fundamentals",
            },
            format="json",
        )
        pending_slot_id = create_response.data["slot"]

        student_schedule = self.client.get(
            reverse("coach-profile-schedule", args=[self.coach.id]), {"date": self.day.isoformat()}
        )
        self.assertEqual([slot["id"] for slot in student_schedule.data["slots"]], [pending_slot_id])
        self.assertEqual(student_schedule.data["slots"][0]["viewer_booking_request_status"], "pending")
        self.assertTrue(student_schedule.data["slots"][0]["viewer_can_cancel"])
        self.assertEqual(len(student_schedule.data["proposal_windows"]), 1)

        self.client.force_authenticate(user=self.coach_user)
        coach_schedule = self.client.get(
            reverse("coach-profile-schedule", args=[self.coach.id]), {"date": self.day.isoformat()}
        )
        self.assertEqual([slot["id"] for slot in coach_schedule.data["slots"]], [pending_slot_id])

        for unrelated_user in (self.other_student_user, self.other_coach_user):
            self.client.force_authenticate(user=unrelated_user)
            unrelated_schedule = self.client.get(
                reverse("coach-profile-schedule", args=[self.coach.id]), {"date": self.day.isoformat()}
            )
            self.assertEqual(unrelated_schedule.data["slots"], [])
            self.assertEqual(len(unrelated_schedule.data["proposal_windows"]), 1)

    def test_multiple_students_can_request_the_same_pending_time(self):
        payload = {
            "proposal_window": self.proposal_window.id,
            "starts_at": self.aware_at(14, 15).isoformat(),
            "ends_at": self.aware_at(15, 45).isoformat(),
            "requested_topic": "Fundamentals",
        }
        self.client.force_authenticate(user=self.student_user)
        first = self.client.post(reverse("coach-profile-request-class", args=[self.coach.id]), payload, format="json")
        self.client.force_authenticate(user=self.other_student_user)
        second = self.client.post(reverse("coach-profile-request-class", args=[self.coach.id]), payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            AvailabilitySlot.objects.filter(status=AvailabilitySlot.Status.PENDING).count(),
            2,
        )
        self.proposal_window.refresh_from_db()
        self.assertTrue(self.proposal_window.active)

    def test_accepting_non_overlapping_requests_consumes_each_part_of_the_window(self):
        self.client.force_authenticate(user=self.student_user)
        first = self.client.post(
            reverse("coach-profile-request-class", args=[self.coach.id]),
            {
                "proposal_window": self.proposal_window.id,
                "starts_at": self.aware_at(14).isoformat(),
                "ends_at": self.aware_at(15).isoformat(),
                "requested_topic": "Fundamentals",
            },
            format="json",
        )
        self.client.force_authenticate(user=self.other_student_user)
        second = self.client.post(
            reverse("coach-profile-request-class", args=[self.coach.id]),
            {
                "proposal_window": self.proposal_window.id,
                "starts_at": self.aware_at(16).isoformat(),
                "ends_at": self.aware_at(17).isoformat(),
                "requested_topic": "Technique review",
            },
            format="json",
        )
        self.client.force_authenticate(user=self.coach_user)

        self.assertEqual(
            self.client.post(reverse("booking-request-accept", args=[first.data["id"]])).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.client.post(reverse("booking-request-accept", args=[second.data["id"]])).status_code,
            status.HTTP_201_CREATED,
        )

        active_windows = ProposalWindow.objects.filter(coach=self.coach, active=True)
        self.assertEqual(active_windows.count(), 1)
        self.assertEqual(active_windows.get().starts_at, self.aware_at(15))
        self.assertEqual(active_windows.get().ends_at, self.aware_at(16))

    def test_student_cannot_request_outside_proposal_window(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("coach-profile-request-class", args=[self.coach.id]),
            {
                "proposal_window": self.proposal_window.id,
                "starts_at": self.aware_at(13).isoformat(),
                "ends_at": self.aware_at(14).isoformat(),
                "requested_topic": "Fundamentals",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AvailabilitySlot.objects.exists())
