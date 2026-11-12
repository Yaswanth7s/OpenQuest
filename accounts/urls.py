
from django.urls import path
from . import views


urlpatterns = [

    path(
        'register/individual/',
        views.register_individual,
        name='register_individual'
    ),

    path(
        'register/organization/',
        views.register_organization,
        name='register_organization'
    ),

]
