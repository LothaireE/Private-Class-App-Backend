from rest_framework import exceptions, permissions, viewsets

from .models import BlockedStudent, CoachProfile, Discipline, StudentProfile
from .permissions import IsProfileOwnerOrReadOnly
from .serializers import BlockedStudentSerializer, CoachProfileSerializer, DisciplineSerializer, StudentProfileSerializer


class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [permissions.AllowAny]


class CoachProfileViewSet(viewsets.ModelViewSet):
    serializer_class = CoachProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    def get_queryset(self):
        return CoachProfile.objects.select_related("user").prefetch_related("disciplines")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrReadOnly]

    def get_queryset(self):
        return StudentProfile.objects.select_related("user").prefetch_related("disciplines")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BlockedStudentViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedStudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlockedStudent.objects.select_related("coach", "student").filter(coach__user=self.request.user)

    def perform_create(self, serializer):
        try:
            coach_profile = self.request.user.coach_profile
        except CoachProfile.DoesNotExist as exc:
            raise exceptions.PermissionDenied("Only users with a coach profile can block students.") from exc
        serializer.save(coach=coach_profile)
