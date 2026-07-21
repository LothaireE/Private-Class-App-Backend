from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.bookings.views import BookingRequestViewSet, SessionViewSet, StudentNoteViewSet
from apps.notifications.views import NotificationViewSet
from apps.profiles.views import BlockedStudentViewSet, CoachProfileViewSet, DisciplineViewSet, StudentProfileViewSet
from apps.scheduling.views import AvailabilitySlotViewSet

router = DefaultRouter()
router.register("disciplines", DisciplineViewSet, basename="discipline")
router.register("coach-profiles", CoachProfileViewSet, basename="coach-profile")
router.register("student-profiles", StudentProfileViewSet, basename="student-profile")
router.register("blocked-students", BlockedStudentViewSet, basename="blocked-student")
router.register("availability-slots", AvailabilitySlotViewSet, basename="availability-slot")
router.register("booking-requests", BookingRequestViewSet, basename="booking-request")
router.register("sessions", SessionViewSet, basename="session")
router.register("student-notes", StudentNoteViewSet, basename="student-note")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
