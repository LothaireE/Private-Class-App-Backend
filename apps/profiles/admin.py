from django.contrib import admin

from .models import BlockedStudent, CoachProfile, Discipline, StudentProfile


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "city", "accepts_new_students", "hourly_rate_cents", "currency")
    list_filter = ("accepts_new_students", "city", "disciplines")
    search_fields = ("display_name", "user__email", "academy_or_club")
    filter_horizontal = ("disciplines",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "city")
    list_filter = ("city", "disciplines")
    search_fields = ("display_name", "user__email")
    filter_horizontal = ("disciplines",)


@admin.register(BlockedStudent)
class BlockedStudentAdmin(admin.ModelAdmin):
    list_display = ("coach", "student", "created_at")
    search_fields = ("coach__display_name", "student__display_name")
