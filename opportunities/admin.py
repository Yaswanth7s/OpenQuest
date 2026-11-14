from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Opportunity, Application


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'organization',
        'opportunity_type',
        'work_mode',
        'status',
        'application_deadline',
        'created_at',
    )

    list_filter = (
        'opportunity_type',
        'work_mode',
        'status',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'organization__organization_name',
    )

    ordering = ('-created_at',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    fields = (
        'applicant',
        'opportunity',
        'cover_letter',
        'resume_download',
        'status',
        'applied_at',
        'updated_at',
    )
    readonly_fields = (
        'resume_download',
        'applied_at',
        'updated_at',
    )

    list_display = (
        'id',
        'applicant',
        'opportunity',
        'status',
        'applied_at',
    )

    list_filter = (
        'status',
        'applied_at',
    )

    search_fields = (
        'applicant__username',
        'opportunity__title',
    )

    ordering = ('-applied_at',)

    @admin.display(description='Resume')
    def resume_download(self, application):
        if not application.resume:
            return 'No resume attached'
        return format_html(
            '<a href="{}">Download resume</a>',
            reverse('download_resume', args=(application.pk,)),
        )