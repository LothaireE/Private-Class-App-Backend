from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.profiles.models import CoachProfile, StudentProfile


class AccountMeApiTests(APITestCase):
    def test_me_requires_authentication(self):
        response = self.client.get(reverse("account-me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_user_and_profile_ids(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="password",
            role=User.Role.BOTH,
            phone="+491234",
        )
        coach = CoachProfile.objects.create(user=user, display_name="Coach Member")
        student = StudentProfile.objects.create(user=user, display_name="Student Member")
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("account-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "member@example.com")
        self.assertEqual(response.data["coach_profile_id"], coach.id)
        self.assertEqual(response.data["student_profile_id"], student.id)
