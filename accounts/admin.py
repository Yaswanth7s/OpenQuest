from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.utils.html import format_html
from .models import User, Profile, OrganizationProfile


class AdminUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'role',
            'organization_status',
            'is_email_verified',
        )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'role',
                'organization_status',
                'is_email_verified',
                'password1',
                'password2',
            ),
        }),
    )

    fieldsets = UserAdmin.fieldsets + (
        ('OpenQuest Information', {
            'fields': (
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
    actions = ('approve_organizations', 'reject_organizations')

    list_display = (
        'id',
        'organization_name',
        'user',
        'organization_status',
        'organization_email',
        'registration_number',
        'created_at'
    )

    search_fields = (
        'organization_name',
        'organization_email',
        'registration_number'
    )

    list_filter = ('user__organization_status', 'created_at')
    fields = (
        'organization_name',
        'user',
        'description',
        'official_website',
        'organization_email',
        'registration_number',
        'verification_document_link',
        'admin_remarks',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'verification_document_link',
        'created_at',
        'updated_at',
    )

    @admin.display(description='Verification status')
    def organization_status(self, profile):
        return profile.user.get_organization_status_display()

    @admin.display(description='Verification document')
    def verification_document_link(self, profile):
        if not profile.verification_document:
            return 'No document uploaded'
        return format_html(
            '<a href="{}">Download verification document</a>',
            reverse(
                'download_verification_document',
                args=(profile.pk,),
            ),
        )

    @admin.action(description='Approve selected organizations')
    def approve_organizations(self, request, queryset):
        updated = User.objects.filter(
            pk__in=queryset.values('user_id'),
            role=User.Role.ORGANIZATION,
        ).update(organization_status=User.OrganizationStatus.APPROVED)
        self.message_user(
            request,
            f'{updated} organization(s) approved.',
            messages.SUCCESS,
        )

    @admin.action(description='Reject selected organizations')
    def reject_organizations(self, request, queryset):
        updated = User.objects.filter(
            pk__in=queryset.values('user_id'),
            role=User.Role.ORGANIZATION,
        ).update(organization_status=User.OrganizationStatus.REJECTED)
        self.message_user(
            request,
            f'{updated} organization(s) rejected.',
            messages.SUCCESS,
        )