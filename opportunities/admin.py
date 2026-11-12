from django.contrib import admin
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