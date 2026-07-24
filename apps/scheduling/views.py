from django.db.models import Q
from rest_framework import permissions, viewsets

from .models import AvailabilitySlot, ProposalWindow
from .permissions import IsSlotCoachOrReadOnly
from .serializers import AvailabilitySlotSerializer, ProposalWindowSerializer


class AvailabilitySlotViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsSlotCoachOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return AvailabilitySlot.objects.select_related("coach", "discipline").filter(
            ~Q(status=AvailabilitySlot.Status.PENDING)
            | Q(
                status=AvailabilitySlot.Status.PENDING,
                booking_requests__status="pending",
                booking_requests__coach__user=user,
            )
            | Q(
                status=AvailabilitySlot.Status.PENDING,
                booking_requests__status="pending",
                booking_requests__student__user=user,
            )
        ).distinct()


class ProposalWindowViewSet(viewsets.ModelViewSet):
    serializer_class = ProposalWindowSerializer
    permission_classes = [permissions.IsAuthenticated, IsSlotCoachOrReadOnly]

    def get_queryset(self):
        queryset = ProposalWindow.objects.select_related("coach")
        coach_id = self.request.query_params.get("coach")
        return queryset.filter(coach_id=coach_id) if coach_id else queryset
