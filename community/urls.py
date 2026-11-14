from django.urls import path

from . import views


app_name = 'community'

urlpatterns = [
    path('', views.challenge_list, name='challenge_list'),
    path('create/', views.create_challenge, name='create_challenge'),
    path('<int:challenge_id>/', views.challenge_detail, name='challenge_detail'),
    path('<int:challenge_id>/comment/', views.add_comment, name='add_comment'),
    path(
        '<int:challenge_id>/status/',
        views.update_challenge_status,
        name='update_challenge_status',
    ),
    path(
        '<int:challenge_id>/teams/create/',
        views.create_team,
        name='create_team',
    ),
    path(
        '<int:challenge_id>/teams/<int:team_id>/join/',
        views.join_team,
        name='join_team',
    ),
    path(
        '<int:challenge_id>/teams/<int:team_id>/submit/',
        views.submit_project,
        name='submit_project',
    ),
    path(
        '<int:challenge_id>/submissions/<int:submission_id>/review/',
        views.review_submission,
        name='review_submission',
    ),
    path(
        '<int:challenge_id>/submissions/<int:submission_id>/attachment/',
        views.download_submission_attachment,
        name='download_submission_attachment',
    ),
]
