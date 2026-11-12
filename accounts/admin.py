from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, OrganizationProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('CampusCollab Information', {
            'fields': (
                'role',
                'organization_status',
                'is_email_verified',
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CampusCollab Information', {
            'fields': (
                'email',
                'role',
                'organization_status',
                'is_email_verified',
            )
        }),
    )

    list_display = (
        'username',
        'email',
        'role',
        'organization_status',
        'is_email_verified',
        'is_staff'
    )

    list_filter = (
        'role',
        'organization_status',
        'is_email_verified',
        'is_staff'
    )

    search_fields = ('username', 'email')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'location', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('created_at',)


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'organization_name',
        'user',
        'organization_email',
        'registration_number',
        'created_at'
    )

    search_fields = (
        'organization_name',
        'organization_email',
        'registration_number'
    )

    list_filter = ('created_at',)