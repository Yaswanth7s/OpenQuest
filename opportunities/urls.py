
from django.urls import path
from . import views


urlpatterns = [

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
