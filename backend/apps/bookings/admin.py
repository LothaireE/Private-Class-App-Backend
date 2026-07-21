from django.contrib import admin

from .models import BookingRequest, Cancellation, Session, StudentNote


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "coach", "slot", "status", "created_at")
    list_filter = ("status", "coach")
    search_fields = ("student__display_name", "coach__display_name", "message", "requested_topic")
    date_hierarchy = "created_at"


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("coach", "student", "starts_at", "ends_at", "status", "topic", "location")
    list_filter = ("status", "coach")
    search_fields = ("student__display_name", "coach__display_name", "topic", "location")
    date_hierarchy = "starts_at"


@admin.register(Cancellation)
class CancellationAdmin(admin.ModelAdmin):
    list_display = ("session", "cancelled_by", "user", "created_at")
    list_filter = ("cancelled_by",)
    search_fields = ("session__coach__display_name", "session__student__display_name", "reason")


@admin.register(StudentNote)
class StudentNoteAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "created_at")
    search_fields = ("student__display_name", "body")
