from django.contrib import admin

from .models import AvailabilitySlot


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("coach", "starts_at", "ends_at", "status", "capacity", "topic", "location")
    list_filter = ("status", "coach", "discipline")
    search_fields = ("coach__display_name", "topic", "location")
    date_hierarchy = "starts_at"
