
from pathlib import Path

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404

from .forms import (
    IndividualRegistrationForm,
    OrganizationRegistrationForm,
    OrganizationProfileForm,
    ProfileForm,
)

from .models import OrganizationProfile, Profile


def register_choice(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'accounts/register_choice.html')


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'profile': profile},
    )


@login_required
def download_verification_document(request, profile_id):
    profile = get_object_or_404(OrganizationProfile, pk=profile_id)
    if not (request.user.is_staff or request.user.id == profile.user_id):
        raise PermissionDenied
    if not profile.verification_document:
        raise Http404('No verification document was uploaded.')
    try:
        document = profile.verification_document.open('rb')
    except FileNotFoundError as error:
        raise Http404('The verification document is no longer available.') from error

    response = FileResponse(
        document,
        as_attachment=True,
        filename=Path(profile.verification_document.name).name,
        content_type='application/octet-stream',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response

def register_individual(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = IndividualRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Your individual account has been created successfully!"
            )

            return redirect('home')

    else:
        form = IndividualRegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'account_type': 'Individual'
        }
    )


def register_organization(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = OrganizationRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Your organization account has been created. "
                "Complete your organization profile while verification is pending."
            )

            login(request, user)

            return redirect('home')

    else:
        form = OrganizationRegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'account_type': 'Organization'
        }
    )



@login_required
def complete_organization_profile(request):

    if request.user.role != 'ORGANIZATION':
        messages.error(
            request,
            "Only organization accounts can complete an organization profile."
        )
        return redirect('home')

    if request.user.organization_status not in (
        'PENDING',
        'REJECTED',
    ):
        messages.error(
            request,
            "Your organization profile cannot be submitted in its current status."
        )
        return redirect('home')

    organization_profile = OrganizationProfile.objects.filter(
        user=request.user
    ).first()

    if request.method == 'POST':

        form = OrganizationProfileForm(
            request.POST,
            request.FILES,
            instance=organization_profile
        )

        if form.is_valid():

            profile = form.save(commit=False)
            profile.user = request.user

            try:
                profile.full_clean()
                profile.save()
                if request.user.organization_status == 'REJECTED':
                    request.user.organization_status = 'PENDING'
                    request.user.save(update_fields=('organization_status',))

                messages.success(
                    request,
                    "Organization profile submitted successfully! "
                    "Your account is awaiting admin verification."
                )

                return redirect('home')

            except ValidationError as error:
                form.add_error(None, str(error))

    else:
        form = OrganizationProfileForm(
            instance=organization_profile
        )

    return render(
        request,
        'accounts/complete_organization_profile.html',
        {'form': form}
    )

