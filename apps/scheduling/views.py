from rest_framework import permissions, viewsets

from .models import AvailabilitySlot
from .permissions import IsSlotCoachOrReadOnly
from .serializers import AvailabilitySlotSerializer


class AvailabilitySlotViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsSlotCoachOrReadOnly]

    def get_queryset(self):
        return AvailabilitySlot.objects.select_related("coach", "discipline")
