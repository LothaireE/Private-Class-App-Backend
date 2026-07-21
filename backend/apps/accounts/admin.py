from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Coaching profile fields", {"fields": ("role", "phone", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Coaching profile fields", {"fields": ("email", "role", "phone", "avatar")}),
    )
