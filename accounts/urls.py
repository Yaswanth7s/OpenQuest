
from django.urls import reverse_lazy
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html',
            redirect_authenticated_user=True,
            next_page='home'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='home'),
        name='logout'
    ),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),

    path(
        'password-reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),

    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),

    path(
        'profile/',
        views.edit_profile,
        name='profile'
    ),

    path(
        'organization-profile/<int:profile_id>/verification-document/',
        views.download_verification_document,
        name='download_verification_document'
    ),

    path(
        'register/individual/',
        views.register_individual,
        name='register_individual'
    ),

    path(
        'register/',
        views.register_choice,
        name='register'
    ),

    path(
        'register/organization/',
        views.register_organization,
        name='register_organization'
    ),

    path(
        'organization/profile/complete/',
        views.complete_organization_profile,
        name='complete_organization_profile'
    ),

]
