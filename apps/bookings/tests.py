from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.bookings.models import BookingRequest, Session, StudentNote
from apps.notifications.models import Notification
from apps.profiles.models import CoachProfile, StudentProfile
from apps.scheduling.models import AvailabilitySlot


class BookingApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.coach_user = User.objects.create_user(
            username="coach",
            email="coach@example.com",
            password="password",
            role=User.Role.COACH,
        )
        self.student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="password",
            role=User.Role.STUDENT,
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password",
            role=User.Role.STUDENT,
        )
        self.coach = CoachProfile.objects.create(user=self.coach_user, display_name="Coach")
        self.student = StudentProfile.objects.create(user=self.student_user, display_name="Student")
        self.other_student = StudentProfile.objects.create(user=self.other_user, display_name="Other")
        self.slot = AvailabilitySlot.objects.create(
            coach=self.coach,
            starts_at=timezone.now() + timedelta(days=1),
            ends_at=timezone.now() + timedelta(days=1, hours=1),
            topic="Guard passing",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_booking(self):
        return BookingRequest.objects.create(slot=self.slot, coach=self.coach, student=self.student)

    def test_student_booking_request_creates_coach_notification(self):
        self.authenticate(self.student_user)

        response = self.client.post(
            reverse("booking-request-list"),
            {
                "slot": self.slot.id,
                "coach": self.coach.id,
                "student": self.student.id,
                "requested_topic": "Half guard",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(user=self.coach_user)
        self.assertEqual(notification.kind, Notification.Kind.BOOKING_REQUESTED)
        self.assertEqual(notification.data["booking_request_id"], response.data["id"])

    def test_student_cannot_create_booking_for_another_student_profile(self):
        self.authenticate(self.student_user)

        response = self.client.post(
            reverse("booking-request-list"),
            {"slot": self.slot.id, "coach": self.coach.id, "student": self.other_student.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(BookingRequest.objects.exists())

    def test_booking_list_is_limited_to_participants(self):
        booking = self.create_booking()
        other_slot = AvailabilitySlot.objects.create(
            coach=self.coach,
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=1),
        )
        BookingRequest.objects.create(slot=other_slot, coach=self.coach, student=self.other_student)
        self.authenticate(self.student_user)

        response = self.client.get(reverse("booking-request-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [booking.id])

    def test_only_coach_can_accept_booking_and_student_is_notified(self):
        booking = self.create_booking()
        self.authenticate(self.student_user)

        denied = self.client.post(reverse("booking-request-accept", args=[booking.id]))

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.coach_user)
        response = self.client.post(reverse("booking-request-accept", args=[booking.id]))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(booking.status, BookingRequest.Status.ACCEPTED)
        self.assertEqual(self.slot.status, AvailabilitySlot.Status.RESERVED)
        notification = Notification.objects.get(user=self.student_user, kind=Notification.Kind.BOOKING_ACCEPTED)
        self.assertEqual(notification.data["session_id"], response.data["id"])

    def test_reject_booking_notifies_student(self):
        booking = self.create_booking()
        self.authenticate(self.coach_user)

        response = self.client.post(reverse("booking-request-reject", args=[booking.id]), {"reason": "Unavailable"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingRequest.Status.REJECTED)
        self.assertTrue(Notification.objects.filter(user=self.student_user, kind=Notification.Kind.BOOKING_REJECTED).exists())

    def test_session_cancel_notifies_other_participant(self):
        booking = self.create_booking()
        self.authenticate(self.coach_user)
        accept_response = self.client.post(reverse("booking-request-accept", args=[booking.id]))
        session_id = accept_response.data["id"]

        response = self.client.post(reverse("session-cancel", args=[session_id]), {"reason": "Sick"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = Session.objects.get(id=session_id)
        self.assertEqual(session.status, Session.Status.CANCELLED)
        notification = Notification.objects.get(user=self.student_user, kind=Notification.Kind.SESSION_CANCELLED)
        self.assertEqual(notification.data["cancelled_by"], "coach")


    def test_booking_response_includes_slot_summary(self):
        booking = self.create_booking()
        self.authenticate(self.student_user)

        response = self.client.get(reverse("booking-request-detail", args=[booking.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["coach_display_name"], "Coach")
        self.assertEqual(response.data["student_display_name"], "Student")
        self.assertEqual(response.data["slot_topic"], "Guard passing")
        self.assertEqual(response.data["slot_status"], AvailabilitySlot.Status.OPEN)
        self.assertIn("slot_starts_at", response.data)
        self.assertIn("slot_ends_at", response.data)

    def test_student_notes_are_private_to_owner(self):
        booking = self.create_booking()
        self.authenticate(self.coach_user)
        session_id = self.client.post(reverse("booking-request-accept", args=[booking.id])).data["id"]
        session = Session.objects.get(id=session_id)
        StudentNote.objects.create(session=session, student=self.student, body="Worked on frames")

        self.authenticate(self.other_user)
        response = self.client.get(reverse("student-note-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
