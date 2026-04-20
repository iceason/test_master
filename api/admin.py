from django.contrib import admin
from .models import RegistrationInvite


@admin.register(RegistrationInvite)
class RegistrationInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'created_by', 'created_at', 'expires_at', 'used_at', 'registered_user')
    readonly_fields = ('token', 'created_at', 'used_at', 'registered_user')
    search_fields = ('token', 'created_by__username', 'registered_user__username')
