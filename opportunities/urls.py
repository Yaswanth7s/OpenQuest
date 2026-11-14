
from django.urls import path
from . import views


urlpatterns = [

    path(
        'applications/mine/',
        views.my_applications,
        name='my_applications'
    ),

    path(
        'organization/dashboard/',
        views.organization_dashboard,
        name='organization_dashboard'
    ),

    path(
        'applications/<int:application_id>/status/',
        views.update_application_status,
        name='update_application_status'
    ),

    path(
        'applications/<int:application_id>/withdraw/',
        views.withdraw_application,
        name='withdraw_application'
    ),

    path(
        'applications/<int:application_id>/resume/',
        views.download_resume,
        name='download_resume'
    ),

    path(
        'create/',
        views.create_opportunity,
        name='create_opportunity'
    ),

    path(
        '<int:opportunity_id>/apply/',
        views.apply_for_opportunity,
        name='apply_for_opportunity'
    ),

]
