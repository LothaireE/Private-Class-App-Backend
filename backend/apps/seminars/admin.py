from django.contrib import admin

from .models import Seminar


@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    list_display = ("title", "coach", "starts_at", "ends_at", "status", "capacity")
    list_filter = ("status", "coach", "discipline")
    search_fields = ("title", "coach__display_name", "location")
    date_hierarchy = "starts_at"
